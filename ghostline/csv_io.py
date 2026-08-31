"""Read records from a CSV. The manual-entry form (§4.7) produces the same Record objects
through `record_from_fields` — one code path, whether a row was parsed or typed."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import Record

_CORE = {"record_id", "name", "phone", "address", "region", "locale"}


def _coerce_claim(value: str) -> object:
    v = value.strip()
    low = v.lower()
    if low in {"true", "yes", "y", "1"}:
        return True
    if low in {"false", "no", "n", "0"}:
        return False
    return v


def record_from_fields(fields: dict[str, str]) -> Record:
    fields = {k.strip(): (v or "").strip() for k, v in fields.items()}
    claims = {
        k: _coerce_claim(v) for k, v in fields.items() if k not in _CORE and v != ""
    }
    return Record(
        record_id=fields.get("record_id") or fields.get("name", "record"),
        name=fields.get("name", ""),
        phone=fields.get("phone", ""),
        address=fields.get("address", ""),
        region=fields.get("region") or None,
        locale=fields.get("locale") or None,
        claims=claims,
    )


def read_records(path: str | Path) -> list[Record]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [record_from_fields(row) for row in csv.DictReader(fh)]
