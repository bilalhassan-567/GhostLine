"""Reliability benchmark — generate `benchmark/results.json`, never hand-write it.

Two sources:
  * replay  — run the pipeline over the labelled fixtures. Deterministic; a sanity floor,
              honestly labelled as fixture-derived, not live calls.
  * live    — run against a CSV of records you own (own test lines) with a `label` column
              giving the human-verified verdict, then compare.

The console and landing page read the resulting file. Displaying a number that was not
generated here is structurally impossible.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from .config import REPO_ROOT
from .extractor import get_extractor
from .models import Verdict
from .replay import load_fixtures, run_fixture

RESULTS_PATH = REPO_ROOT / "benchmark" / "results.json"


def _summarise(pairs: list[tuple[str, str, list[str]]], mode: str) -> dict:
    """pairs = [(expected_verdict, got_verdict, diagnostic_tags), ...]"""
    n = len(pairs)
    agree = sum(1 for exp, got, _ in pairs if exp == got)
    abstained = sum(1 for _, got, _ in pairs if got == Verdict.UNCLEAR.value)
    no_contact = sum(1 for _, got, _ in pairs if got == Verdict.NO_CONTACT.value)
    # Agreement over the calls where a person actually engaged (exclude NO_CONTACT).
    engaged = [(e, g) for e, g, _ in pairs if e != Verdict.NO_CONTACT.value]
    engaged_agree = sum(1 for e, g in engaged if e == g)
    tags = Counter(t for _, _, ts in pairs for t in ts)
    misclassified = [
        {"expected": e, "got": g} for e, g, _ in pairs if e != g and g != Verdict.NO_CONTACT.value
    ]
    return {
        "mode": mode,
        "n_calls": n,
        "human_agreement_rate": round(agree / n, 4) if n else 0.0,
        "engaged_agreement_rate": round(engaged_agree / len(engaged), 4) if engaged else 0.0,
        "abstention_rate": round(abstained / n, 4) if n else 0.0,
        "no_contact_rate": round(no_contact / n, 4) if n else 0.0,
        "failure_taxonomy": dict(tags),
        "misclassified": misclassified,
        "generated_at": datetime.now(UTC).isoformat(),
        "note": (
            "Fixture-derived: the pipeline run against 9 recorded, human-labelled call "
            "transcripts. Not live calls. Replace with `--source live` once real calls exist."
            if mode == "replay"
            else "Live: real calls to lines the operator controls, compared to human labels."
        ),
    }


def run_replay_benchmark() -> dict:
    extractor = get_extractor()
    pairs: list[tuple[str, str, list[str]]] = []
    for fx in load_fixtures():
        res = run_fixture(fx, extractor)
        att = res.attestation
        pairs.append(
            (fx.meta["expected_verdict"], att.verdict.value, [t.value for t in att.diagnostic_tags])
        )
    return _summarise(pairs, "replay")


def run_live_benchmark(csv_path: str | Path) -> dict:
    """CSV needs: name, phone, region, <claim columns>, and a `label` column holding the
    human-verified verdict for the first claim. Requires CALL-E credentials."""
    import csv as _csv

    from .call_engine import CallEngine
    from .claim_pack import load_pack
    from .csv_io import record_from_fields
    from .pipeline import resolve_record
    from .policy_gate import PolicyGate

    settings = None
    gate = PolicyGate()
    engine = CallEngine()
    extractor = get_extractor()
    pairs: list[tuple[str, str, list[str]]] = []
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        rows = list(_csv.DictReader(fh))
    for row in rows:
        label = (row.pop("label", "") or "").strip().upper()
        pack = load_pack(row.pop("pack", "healthcare"))
        rec = record_from_fields(row)
        res = gate.authorize(rec, pack, dry_run=False)
        if not res.allowed:
            pairs.append(("", Verdict.NO_CONTACT.value, ["BLOCKED"]))
            continue
        transcript = engine.place(res.plan)
        atts = resolve_record(rec, pack, transcript, extractor)
        got = atts[0].verdict.value if atts else Verdict.NO_CONTACT.value
        pairs.append((label, got, [t.value for a in atts for t in a.diagnostic_tags]))
    _ = settings
    return _summarise(pairs, "live")


def write_results(results: dict, path: Path = RESULTS_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return path


def load_results(path: Path = RESULTS_PATH) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
