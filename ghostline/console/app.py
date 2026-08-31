"""Ghostline web console — one screen: record -> call -> evidence -> verdict -> correction.

Two ways in, same engine (master doc §4.7): upload a CSV, or type one record into the form.
Replay Mode explores the canned fixture scenarios with zero live calls.

    uvicorn ghostline.console.app:app --reload
"""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from ..claim_pack import list_packs, load_pack
from ..config import get_settings
from ..corrections import corrections_csv_str
from ..csv_io import record_from_fields
from ..models import CallOutcome, Record, Verdict
from ..replay import load_fixtures
from . import runs

# On a serverless host (Vercel) there are no background workers, so the poll-based live
# call flow is unavailable until the webhook-driven path ships. Replay Mode works everywhere.
_LIVE_DISABLED = bool(os.environ.get("VERCEL")) and not os.environ.get("GHOSTLINE_WEBHOOK_BASE")
_LIVE_DISABLED_MSG = (
    "Live calling isn't available on this hosted instance yet (it needs a webhook receiver). "
    "Explore every verdict state in Replay Mode, or run the console locally "
    "(uvicorn ghostline.console.app:app) or the CLI (ghostline verify ... --live)."
)

app = FastAPI(title="Ghostline")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

_CHIP_CLASS = {
    Verdict.MATCH: "match",
    Verdict.MISMATCH: "mismatch",
    Verdict.UNCLEAR: "unclear",
    Verdict.NO_CONTACT: "nocontact",
}
templates.env.globals["chip_class"] = lambda v: _CHIP_CLASS.get(v, "")
templates.env.globals["CallOutcome"] = CallOutcome


def _highlight(text: str, span: str | None) -> Markup:
    """Escape a transcript turn, then wrap the (escaped) evidence span in <mark>."""
    safe = str(escape(text))
    if span and span in text:
        safe_span = str(escape(span))
        safe = safe.replace(safe_span, f"<mark>{safe_span}</mark>")
    return Markup(safe)  # inputs are escaped above


templates.env.globals["highlight"] = _highlight


@app.get("/health")
def health() -> JSONResponse:
    s = get_settings()
    return JSONResponse(
        {
            "status": "ok",
            "mode": s.mode,
            "calle_configured": s.has_calle,
            "llm_configured": s.has_llm,
            "packs": [p.ref for p in list_packs()],
        }
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    pack = load_pack("healthcare")
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "packs": list_packs(),
            "pack": pack,
            "settings": get_settings(),
            "live_disabled": _LIVE_DISABLED,
            "scenarios": [
                (fx.path.stem, fx.meta.get("scenario", fx.path.stem)) for fx in load_fixtures()
            ],
        },
    )


@app.post("/verify")
async def verify(
    request: Request,
    mode: str = Form("replay"),
    pack: str = Form("healthcare"),
    name: str = Form(""),
    phone: str = Form(""),
    region: str = Form("US"),
    csv_file: UploadFile | None = None,
):
    form = await request.form()
    records = _records_from_request(form, name, phone, region, pack, csv_file)

    if mode == "live":
        if not records:
            return RedirectResponse("/?error=no-record", status_code=303)
        if _LIVE_DISABLED:
            return templates.TemplateResponse(
                request, "notice.html", {"message": _LIVE_DISABLED_MSG}, status_code=503
            )
        run = runs.start_live_run(records, pack, credits_remaining=None)
        return RedirectResponse(f"/run/{run.id}", status_code=303)

    # Replay: synchronous, render directly — no run store needed (works on serverless).
    run = runs.start_replay_run()
    return templates.TemplateResponse(request, "run.html", {"run": run})


@app.get("/replay", response_class=HTMLResponse)
def replay_all(request: Request):
    return templates.TemplateResponse(request, "run.html", {"run": runs.start_replay_run()})


@app.get("/replay-corrections.csv")
def replay_corrections():
    run = runs.start_replay_run()
    return _csv_response(run.all_attestations, "corrections-replay.csv")


@app.get("/replay/{scenario}", response_class=HTMLResponse)
def replay_one(request: Request, scenario: str):
    return templates.TemplateResponse(request, "run.html", {"run": runs.start_replay_run(scenario)})


@app.get("/run/{run_id}", response_class=HTMLResponse)
def run_page(request: Request, run_id: str):
    run = runs.get_run(run_id)
    if run is None:
        return HTMLResponse("Run not found.", status_code=404)
    return templates.TemplateResponse(request, "run.html", {"run": run})


@app.get("/api/run/{run_id}")
def run_status(run_id: str):
    run = runs.get_run(run_id)
    if run is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(
        {
            "id": run.id,
            "mode": run.mode,
            "status": run.status,
            "records": [
                {
                    "record_id": rr.record.record_id,
                    "name": rr.record.name,
                    "status": rr.status,
                    "dial": rr.dial_e164,
                    "messages": rr.messages,
                    "verdicts": [
                        {
                            "claim_id": a.claim_id,
                            "verdict": a.verdict.value,
                            "evidence": a.evidence_span,
                            "reason": a.evaluation_reason,
                            "source": a.source_role.value,
                            "confidence": a.confidence.value,
                            "tags": [t.value for t in a.diagnostic_tags],
                            "expires_at": a.expires_at.isoformat() if a.expires_at else None,
                        }
                        for a in rr.attestations
                    ],
                }
                for rr in run.records
            ],
        }
    )


@app.get("/run/{run_id}/corrections.csv")
def corrections_download(run_id: str):
    run = runs.get_run(run_id)
    if run is None:
        return Response("Run not found.", status_code=404)
    return _csv_response(run.all_attestations, f"corrections-{run_id}.csv")


def _csv_response(attestations, filename: str) -> Response:
    return Response(
        corrections_csv_str(attestations),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------------------------------------------------------------------------------
def _records_from_request(form, name, phone, region, pack_id, csv_file) -> list[Record]:
    records: list[Record] = []
    upload = form.get("csv_file")
    if upload is not None and getattr(upload, "filename", ""):
        raw = upload.file.read().decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(raw)):
            records.append(record_from_fields(row))
        return records

    if name.strip() and phone.strip():
        pack = load_pack(pack_id)
        claims: dict[str, object] = {}
        for c in pack.claims:
            v = (form.get(f"claim__{c.claim_id}") or "").strip().lower()
            if v in {"yes", "true"}:
                claims[c.claim_id] = True
            elif v in {"no", "false"}:
                claims[c.claim_id] = False
        records.append(
            Record(
                record_id=name.strip().lower().replace(" ", "_")[:40] or "manual",
                name=name.strip(),
                phone=phone.strip(),
                region=(region or "US").strip() or None,
                claims=claims,
            )
        )
    return records
