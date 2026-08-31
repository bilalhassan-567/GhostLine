"""In-memory store of verification runs + the worker that drives one.

A "run" is one submission (a manual record or an uploaded CSV) resolved against a claim pack.
Live runs execute on a background thread and are polled by the browser; replay runs finish
synchronously. Attestations are also written to the SQLite ledger (`store.Ledger`).
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from ..claim_pack import load_pack
from ..config import get_settings
from ..extractor import get_extractor
from ..models import Attestation, CallOutcome, Record, Transcript
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


@dataclass
class Run:
    id: str
    mode: Mode
    pack_ref: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: str = "running"          # running | done | error
    records: list[RecordRun] = field(default_factory=list)
    error: str | None = None

    @property
    def all_attestations(self) -> list[Attestation]:
        return [a for rr in self.records for a in rr.attestations]


_RUNS: dict[str, Run] = {}
_LOCK = threading.Lock()


def get_run(run_id: str) -> Run | None:
    return _RUNS.get(run_id)


def _put(run: Run) -> None:
    with _LOCK:
        _RUNS[run.id] = run
        # keep memory bounded
        if len(_RUNS) > 200:
            for k in list(_RUNS)[:50]:
                _RUNS.pop(k, None)


# --------------------------------------------------------------------------------------
def start_replay_run(scenario: str | None = None) -> Run:
    """Explore the canned fixture scenarios — zero live calls. Each fixture declares its own
    pack + claim in `_meta`, so this runs the *real* pipeline over recorded transcripts."""
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
        rr.messages.append(fx.meta.get("scenario", ""))
        run.records.append(rr)

    run.pack_ref = chosen[0].meta["pack"] if len(chosen) == 1 else "(fixtures)"
    run.status = "done"
    _ledger_write(run)
    _put(run)
    return run


def start_live_run(records: list[Record], pack_id: str, credits_remaining: int | None) -> Run:
    pack = load_pack(pack_id)
    run = Run(id=uuid.uuid4().hex[:12], mode="live", pack_ref=pack.ref)
    for rec in records:
        run.records.append(RecordRun(record=rec))
    _put(run)
    t = threading.Thread(target=_live_worker, args=(run.id, pack_id, credits_remaining), daemon=True)
    t.start()
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
            rr.messages = list(res.messages)
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
            rr.status = "done"
        run.status = "done"
    except Exception as exc:  # noqa: BLE001 - surface, don't crash the server
        run.status = "error"
        run.error = str(exc)
    finally:
        _ledger_write(run)


def _ledger_write(run: Run) -> None:
    try:
        ledger = Ledger()
        for rr in run.records:
            ledger.record_many(
                rr.attestations, run_id=run.id,
                phone_e164=rr.dial_e164 or rr.record.phone,
            )
        ledger.close()
    except Exception as exc:  # noqa: BLE001 - the ledger is an audit aid, never block a run on it
        print(f"[ghostline] ledger write skipped: {exc!s}")
