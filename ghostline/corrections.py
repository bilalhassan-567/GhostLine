"""The corrections file — the actual product outcome.

A verdict alone is not a deliverable. Every evidence-backed MISMATCH becomes one row someone
can act on Monday morning. UNCLEAR records never silently become corrections (master doc §4.9).
CSV only — one format, on purpose.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable

from .models import Attestation

FIELDS = [
    "record_id",
    "claim_id",
    "field",
    "old_value",
    "new_value",
    "verdict",
    "evidence",
    "source",
    "confidence",
    "attested_at",
    "expires_at",
    "call_id",
]


def _row(att: Attestation) -> dict[str, object]:
    observed = att.answer_text or (att.calle_structured_result or {}).get(att.claim_id, "")
    return {
        "record_id": att.record_id,
        "claim_id": att.claim_id,
        "field": att.claim_id,
        "old_value": att.asserted_value,
        "new_value": observed,
        "verdict": att.verdict.value,
        "evidence": att.evidence_span or "",
        "source": att.source_role.value,
        "confidence": att.confidence.value,
        "attested_at": att.attested_at.isoformat(),
        "expires_at": att.expires_at.isoformat() if att.expires_at else "",
        "call_id": att.call_id or "",
    }


def corrections_rows(attestations: Iterable[Attestation]) -> list[dict[str, object]]:
    return [_row(a) for a in attestations if a.is_correction]


def write_corrections_csv(attestations: Iterable[Attestation], path) -> int:
    rows = corrections_rows(attestations)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def corrections_csv_str(attestations: Iterable[Attestation]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(corrections_rows(attestations))
    return buf.getvalue()
