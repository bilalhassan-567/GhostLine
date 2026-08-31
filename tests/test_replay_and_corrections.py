"""All 9 replay fixtures resolve to their expected verdict; corrections exclude UNCLEAR."""

import pytest

from ghostline.corrections import corrections_rows
from ghostline.extractor import HeuristicExtractor
from ghostline.models import Verdict
from ghostline.replay import load_fixtures, run_fixture

FIXTURES = load_fixtures()


@pytest.mark.parametrize("fx", FIXTURES, ids=[f.path.stem for f in FIXTURES])
def test_fixture_resolves_as_expected(fx):
    res = run_fixture(fx, HeuristicExtractor())
    assert res.ok, res.detail


def test_all_nine_fixtures_present():
    assert len(FIXTURES) == 9


def test_corrections_only_contains_evidence_backed_mismatch():
    atts = [run_fixture(fx, HeuristicExtractor()).attestation for fx in FIXTURES]
    rows = corrections_rows(atts)
    # exactly one MISMATCH fixture (02); nothing else
    assert len(rows) == 1
    assert rows[0]["record_id"] == "provider_002"
    assert rows[0]["verdict"] == "MISMATCH"
    assert rows[0]["evidence"]  # non-empty verbatim span
    # no UNCLEAR / NO_CONTACT attestation leaked into corrections
    for att in atts:
        if att.verdict != Verdict.MISMATCH:
            assert att.record_id not in {r["record_id"] for r in rows}


def test_unclear_never_becomes_a_correction():
    for fx in FIXTURES:
        att = run_fixture(fx, HeuristicExtractor()).attestation
        if att.verdict == Verdict.UNCLEAR:
            assert not att.is_correction
