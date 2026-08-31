"""Cross-instance run store.

On a single always-on process (local `uvicorn`) an in-process dict is enough. On serverless
(Vercel) each request may hit a different instance, so runs are kept in Upstash Redis when
`UPSTASH_REDIS_REST_URL` + `UPSTASH_REDIS_REST_TOKEN` are set (free tier, no card). The API
here is the same either way: `save(run)`, `load(run_id)`.
"""

from __future__ import annotations

import json
import os
import re
import time

import httpx

_KEY_RE = re.compile(r"[^a-zA-Z0-9_-]")

from ..derived import DerivedProposal
from ..models import Attestation, Record, Transcript
from .runs import RecordRun, Run

_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
_TTL_S = 60 * 60 * 24 * 40  # survive the judging window
_mem: dict[str, str] = {}


def _set(key: str, value: str) -> None:
    if _URL and _TOKEN:
        httpx.post(
            f"{_URL}/set/{key}",
            headers={"Authorization": f"Bearer {_TOKEN}"},
            params={"EX": _TTL_S},
            content=value.encode(),
            timeout=8,
        ).raise_for_status()
    else:
        _mem[key] = value
        if len(_mem) > 500:
            for k in list(_mem)[:100]:
                _mem.pop(k, None)


def _get(key: str) -> str | None:
    if _URL and _TOKEN:
        try:
            resp = httpx.get(
                f"{_URL}/get/{key}", headers={"Authorization": f"Bearer {_TOKEN}"}, timeout=8
            )
            resp.raise_for_status()
            return resp.json().get("result")
        except httpx.HTTPError:
            return None
    return _mem.get(key)


# --------------------------------------------------------------------------------------
def _rr_to_dict(rr: RecordRun) -> dict:
    return {
        "record": rr.record.model_dump(mode="json"),
        "status": rr.status,
        "messages": rr.messages,
        "transcript": rr.transcript.model_dump(mode="json") if rr.transcript else None,
        "attestations": [a.model_dump(mode="json") for a in rr.attestations],
        "dial_e164": rr.dial_e164,
        "derived": vars(rr.derived) if rr.derived else None,
        "trust": rr.trust,
    }


def _rr_from_dict(d: dict) -> RecordRun:
    rr = RecordRun(record=Record.model_validate(d["record"]))
    rr.status = d["status"]
    rr.messages = d["messages"]
    rr.transcript = Transcript.model_validate(d["transcript"]) if d.get("transcript") else None
    rr.attestations = [Attestation.model_validate(a) for a in d.get("attestations", [])]
    rr.dial_e164 = d.get("dial_e164")
    rr.derived = DerivedProposal(**d["derived"]) if d.get("derived") else None
    rr.trust = d.get("trust")
    return rr


def to_dict(run: Run) -> dict:
    return {
        "id": run.id,
        "mode": run.mode,
        "pack_ref": run.pack_ref,
        "status": run.status,
        "error": run.error,
        "summary": run.summary,
        "saved_at": time.time(),
        "records": [_rr_to_dict(rr) for rr in run.records],
    }


def from_dict(d: dict) -> Run:
    run = Run(id=d["id"], mode=d["mode"], pack_ref=d["pack_ref"])
    run.status = d["status"]
    run.error = d.get("error")
    run.summary = d.get("summary")
    run.records = [_rr_from_dict(rr) for rr in d.get("records", [])]
    return run


def _key(run_id: str) -> str:
    return "gl:run:" + _KEY_RE.sub("", run_id)[:64]


def save(run: Run) -> None:
    _set(_key(run.id), json.dumps(to_dict(run)))


def load(run_id: str) -> Run | None:
    raw = _get(_key(run_id))
    if not raw:
        return None
    try:
        return from_dict(json.loads(raw))
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def enabled() -> bool:
    return bool(_URL and _TOKEN)
