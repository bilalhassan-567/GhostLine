"""Append-only attestation ledger (SQLite).

Every resolved claim is written here once, never updated — so "why did Ghostline say this?"
is always answerable, and re-verification leaves the prior attestation intact for a diff.
This is the audit trail behind the trust story; it is not on the hot path of a single call.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from .config import REPO_ROOT
from .models import Attestation


def _default_db() -> Path:
    # Resolved per call so tests / hosts can set GHOSTLINE_DB after import.
    return Path(os.environ.get("GHOSTLINE_DB") or (REPO_ROOT / "ghostline.db"))


DEFAULT_DB = _default_db()  # kept for back-compat / callers that import it

_SCHEMA = """
CREATE TABLE IF NOT EXISTS attestations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT,
    record_id     TEXT NOT NULL,
    claim_id      TEXT NOT NULL,
    pack_ref      TEXT NOT NULL,
    phone_e164    TEXT,
    verdict       TEXT NOT NULL,
    asserted_value TEXT,
    answer_text   TEXT,
    evidence_span TEXT,
    source_role   TEXT,
    confidence    TEXT,
    diagnostic_tags TEXT,
    evaluation_reason TEXT,
    call_id       TEXT,
    provider_call_id TEXT,
    attested_at   TEXT NOT NULL,
    expires_at    TEXT,
    calle_json    TEXT
);
CREATE INDEX IF NOT EXISTS idx_att_record ON attestations(record_id, claim_id);
CREATE INDEX IF NOT EXISTS idx_att_phone ON attestations(phone_e164);
CREATE INDEX IF NOT EXISTS idx_att_run ON attestations(run_id);
"""


class Ledger:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = str(path or _default_db())
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def record(self, att: Attestation, *, run_id: str | None = None, phone_e164: str | None = None) -> int:
        cur = self._conn.execute(
            """INSERT INTO attestations (
                run_id, record_id, claim_id, pack_ref, phone_e164, verdict, asserted_value,
                answer_text, evidence_span, source_role, confidence, diagnostic_tags,
                evaluation_reason, call_id, provider_call_id, attested_at, expires_at, calle_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                run_id, att.record_id, att.claim_id, att.pack_ref, phone_e164,
                att.verdict.value, _s(att.asserted_value), att.answer_text, att.evidence_span,
                att.source_role.value, att.confidence.value,
                json.dumps([t.value for t in att.diagnostic_tags]),
                att.evaluation_reason, att.call_id, att.provider_call_id,
                att.attested_at.isoformat(), att.expires_at.isoformat() if att.expires_at else None,
                json.dumps(att.calle_structured_result) if att.calle_structured_result else None,
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def record_many(self, atts: Iterable[Attestation], **kw) -> list[int]:
        return [self.record(a, **kw) for a in atts]

    def history_for_number(self, phone_e164: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM attestations WHERE phone_e164 = ? ORDER BY attested_at", (phone_e164,)
        ).fetchall()
        return [dict(r) for r in rows]

    def prior_attestation(self, record_id: str, claim_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM attestations WHERE record_id=? AND claim_id=? "
            "ORDER BY attested_at DESC LIMIT 1",
            (record_id, claim_id),
        ).fetchone()
        return dict(row) if row else None

    def trust_score(self, phone_e164: str) -> dict:
        """Cherry (m): aggregate a number's attestation history into a small badge."""
        rows = self.history_for_number(phone_e164)
        resolved = [r for r in rows if r["verdict"] in ("MATCH", "MISMATCH")]
        mismatches = [r for r in rows if r["verdict"] == "MISMATCH"]
        return {
            "times_verified": len(rows),
            "resolved": len(resolved),
            "mismatches": len(mismatches),
            "label": _trust_label(len(rows), len(mismatches)),
        }

    def close(self) -> None:
        self._conn.close()


def _s(v: object) -> str | None:
    return None if v is None else str(v)


def _trust_label(total: int, mismatches: int) -> str:
    if total < 2:
        return "new"
    if mismatches == 0:
        return f"verified {total}x - consistent"
    return f"verified {total}x - {mismatches} change(s) found"
