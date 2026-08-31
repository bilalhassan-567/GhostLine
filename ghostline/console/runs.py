"""In-memory store of verification runs + the worker that drives one.

A "run" is one submission (a manual record or an uploaded CSV) resolved against a claim pack.
Live runs execute on a background thread and are polled by the browser; replay runs finish
synchronously. Attestations are also written to the SQLite ledger (`store.Ledger`).
"""

from __future__ import annotations

import threading
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from ..claim_pack import load_pack
from ..config import get_settings
from ..derived import DerivedProposal, detect
from ..extractor import get_extractor
from ..models import Attestation, CallOutcome, Record, Transcript, Verdict
from ..pipeline import resolve_record
from ..policy_gate import GateDecision, PolicyGate
from ..replay import load_fixtures
from ..store import Ledger

Mode = Literal["replay", "live"]


@dataclass
class RecordRun:
    record: Record
    status: str = "pending"          # pending | dialing | resolving | done | blocked | error
    messages: list[str] = field(default_factory=list)
    transcript: Transcript | None = None
    attestations: list[Attestation] = field(default_factory=list)
    dial_e164: str | None = None
    derived: DerivedProposal | None = None
    trust: dict | None = None         # cherry (m): per-number history badge


@dataclass
class Run:
    id: str
    mode: Mode
    pack_ref: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: str = "running"          # running | done | error
    records: list[RecordRun] = field(default_factory=list)
    error: str | None = None
    summary: str | None = None        # cherry (d): plain-English batch summary

    @property
    def all_attestations(self) -> list[Attestation]:
        return [a for rr in self.records for a in rr.attestations]


_RUNS: dict[str, Run] = {}
_LOCK = threading.Lock()


def get_run(run_id: str) -> Run | None:
    run = _RUNS.get(run_id)
    if run is not None:
        return run
    from . import store_kv  # lazy: avoids an import cycle

    return store_kv.load(run_id)


def _put(run: Run) -> None:
    with _LOCK:
        _RUNS[run.id] = run
        if len(_RUNS) > 200:
            for k in list(_RUNS)[:50]:
                _RUNS.pop(k, None)
    try:
        from . import store_kv

        store_kv.save(run)
    except Exception as exc:  # noqa: BLE001 - KV is a convenience, the dict is the primary
        print(f"[ghostline] kv save skipped: {exc!s}")


# --------------------------------------------------------------------------------------
def duplicate_number_groups(records: list[Record]) -> list[list[str]]:
    """Cherry (g): records that share a phone number - one call can resolve all of them."""
    by_phone: dict[str, list[str]] = {}
    for r in records:
        by_phone.setdefault(r.phone.strip(), []).append(r.record_id)
    return [ids for ids in by_phone.values() if len(ids) > 1]


# --------------------------------------------------------------------------------------
def start_replay_run(scenario: str | None = None) -> Run:
    from ..pipeline import resolve_claim

    run = Run(id=uuid.uuid4().hex[:12], mode="replay", pack_ref="(fixtures)")
    extractor = get_extractor()
    fixtures = {fx.path.stem: fx for fx in load_fixtures()}
    chosen = [fixtures[scenario]] if scenario in fixtures else list(fixtures.values())

    for fx in chosen:
        pack = load_pack(fx.meta["pack"])
        rr = RecordRun(record=fx.record, status="done", transcript=fx.transcript())
        claim = pack.claim(fx.meta["claim_id"])
        rr.attestations = [resolve_claim(fx.record, claim, pack, rr.transcript, extractor)]
        rr.derived = detect(rr.transcript)
        run.records.append(rr)

    run.pack_ref = chosen[0].meta["pack"] if len(chosen) == 1 else "(fixtures)"
    run.status = "done"
    _finalise(run)
    return run


def start_live_run(records: list[Record], pack_id: str, credits_remaining: int | None) -> Run:
    pack = load_pack(pack_id)
    run = Run(id=uuid.uuid4().hex[:12], mode="live", pack_ref=pack.ref)
    for rec in records:
        run.records.append(RecordRun(record=rec))
    for group in duplicate_number_groups(records):
        run.records[0].messages.append(
            f"{len(group)} records share a phone number ({', '.join(group)}) - one call may resolve all."
        )
    _put(run)

    base = get_settings().webhook_base
    if base:
        # Serverless: CALL-E calls us back at /calle/webhook when each call finishes.
        threading.Thread(
            target=_webhook_dispatch, args=(run.id, pack_id, base, credits_remaining), daemon=True
        ).start()
    else:
        threading.Thread(
            target=_live_worker, args=(run.id, pack_id, credits_remaining), daemon=True
        ).start()
    return run


def _webhook_dispatch(run_id: str, pack_id: str, base: str, credits_remaining: int | None) -> None:
    """Place every call with a webhook_url and return. Terminal results arrive at
    app `/calle/webhook` -> resolve_from_webhook()."""
    from ..call_engine import CallEngine

    run = _RUNS[run_id]
    settings = get_settings()
    pack = load_pack(pack_id)
    gate = PolicyGate(settings)
    engine = CallEngine(settings)
    hook = base.rstrip("/") + "/calle/webhook"
    made = 0
    for i, rr in enumerate(run.records):
        res = gate.authorize(
            rr.record, pack, credits_remaining=credits_remaining,
            calls_this_session=made, dry_run=False,
        )
        rr.dial_e164 = res.plan.dial_e164 if res.plan else None
        rr.messages += list(res.messages)
        if res.decision == GateDecision.BLOCK:
            rr.status = "blocked"
            continue
        try:
            engine.dispatch(res.plan, webhook_url=hook, metadata={"gl_run": run_id, "gl_idx": str(i)})
            rr.status = "dialing"
            made += 1
        except Exception as exc:  # noqa: BLE001
            rr.status = "error"
            rr.messages.append(str(exc))
    if not any(rr.status == "dialing" for rr in run.records):
        run.status = "done"
        _finalise(run)
    else:
        _put(run)


def resolve_from_webhook(run_id: str, record_index: int, calltask: dict) -> None:
    from ..calle_normalize import transcript_from_calltask

    run = get_run(run_id)
    if run is None or record_index >= len(run.records):
        return
    rr = run.records[record_index]
    pack = load_pack(run.pack_ref if run.pack_ref not in ("(fixtures)", "") else "healthcare")
    transcript = transcript_from_calltask(calltask)
    rr.transcript = transcript
    if transcript.outcome == CallOutcome.ERROR:
        rr.status = "error"
        rr.messages.append(transcript.failure_message or transcript.failure_code or "error")
    else:
        rr.attestations = resolve_record(rr.record, pack, transcript, get_extractor())
        rr.derived = detect(transcript)
        rr.status = "done"
    if all(r.status in ("done", "error", "blocked") for r in run.records):
        run.status = "done"
        _finalise(run)
    else:
        _put(run)


def start_derived_run(parent_run_id: str, record_index: int, approved_phone: str | None) -> Run | None:
    parent = _RUNS.get(parent_run_id)
    if parent is None or record_index >= len(parent.records):
        return None
    src = parent.records[record_index]
    if src.derived is None:
        return None
    # The dial target: the approved suggestion if the user approved one, else the record's own
    # number. A transcript number only becomes a target here, after an explicit approval.
    rec = src.record.model_copy(deep=True)
    if src.derived.phone and approved_phone == src.derived.phone:
        rec.phone = src.derived.phone
        rec.record_id = f"{rec.record_id}-derived"
    pack_id = parent.pack_ref if parent.pack_ref != "(fixtures)" else "healthcare"
    run = start_live_run([rec], pack_id, credits_remaining=None)
    run.records[0].messages.insert(0, f"Derived from {parent_run_id}: {src.derived.reason}")
    return run


def _live_worker(run_id: str, pack_id: str, credits_remaining: int | None) -> None:
    from ..call_engine import CallEngine

    run = _RUNS[run_id]
    settings = get_settings()
    pack = load_pack(pack_id)
    gate = PolicyGate(settings)
    extractor = get_extractor(settings)
    engine = CallEngine(settings)
    made = 0
    try:
        for rr in run.records:
            res = gate.authorize(
                rr.record, pack, credits_remaining=credits_remaining,
                calls_this_session=made, dry_run=False,
            )
            rr.dial_e164 = res.plan.dial_e164 if res.plan else None
            rr.messages += list(res.messages)
            if res.decision == GateDecision.BLOCK:
                rr.status = "blocked"
                continue
            rr.status = "dialing"
            transcript = engine.place(res.plan)
            made += 1
            rr.transcript = transcript
            if transcript.outcome == CallOutcome.ERROR:
                rr.status = "error"
                rr.messages.append(transcript.failure_message or transcript.failure_code or "error")
                continue
            rr.status = "resolving"
            rr.attestations = resolve_record(rr.record, pack, transcript, extractor)
            rr.derived = detect(transcript)
            rr.status = "done"
        run.status = "done"
    except Exception as exc:  # noqa: BLE001 - surface, don't crash the server
        run.status = "error"
        run.error = str(exc)
    finally:
        _finalise(run)


# --------------------------------------------------------------------------------------
def _finalise(run: Run) -> None:
    _ledger_write(run)
    _attach_trust(run)
    run.summary = _batch_summary(run)
    _put(run)


def _batch_summary(run: Run) -> str:
    counts = Counter(a.verdict for a in run.all_attestations)
    if not counts:
        return ""
    parts = []
    if counts[Verdict.MATCH]:
        parts.append(f"{counts[Verdict.MATCH]} confirmed")
    if counts[Verdict.MISMATCH]:
        parts.append(f"{counts[Verdict.MISMATCH]} changed")
    if counts[Verdict.UNCLEAR]:
        parts.append(f"{counts[Verdict.UNCLEAR]} unclear")
    if counts[Verdict.NO_CONTACT]:
        parts.append(f"{counts[Verdict.NO_CONTACT]} no contact")
    tags = Counter(t.value for a in run.all_attestations for t in a.diagnostic_tags)
    why = ""
    if tags.get("AMBIGUOUS"):
        why = " - most unclear cases were answers that never named the specific claim subject"
    elif tags.get("VOICEMAIL") or tags.get("IVR"):
        why = " - the misses were voicemail and phone menus, not refusals"
    n = len({rr.record.record_id for rr in run.records})
    return f"{n} record(s) verified: " + ", ".join(parts) + why + "."


def _attach_trust(run: Run) -> None:
    try:
        ledger = Ledger()
        for rr in run.records:
            phone = rr.dial_e164 or rr.record.phone
            t = ledger.trust_score(phone)
            if t["times_verified"] > 1:
                rr.trust = t
        ledger.close()
    except Exception as exc:  # noqa: BLE001
        print(f"[ghostline] trust lookup skipped: {exc!s}")


def _ledger_write(run: Run) -> None:
    try:
        ledger = Ledger()
        for rr in run.records:
            ledger.record_many(
                rr.attestations, run_id=run.id, phone_e164=rr.dial_e164 or rr.record.phone
            )
        ledger.close()
    except Exception as exc:  # noqa: BLE001 - the ledger is an audit aid, never block a run on it
        print(f"[ghostline] ledger write skipped: {exc!s}")
