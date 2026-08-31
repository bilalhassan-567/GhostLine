"""The evidence-span-or-abstain rule — the project's load-bearing invariant."""

from datetime import timedelta

import pytest

from ghostline.models import CallOutcome, DiagnosticTag, Extraction, SourceRole, Transcript, Verdict
from ghostline.verdict import VerdictError, evaluate
from tests.conftest import convo


def test_no_span_forces_unclear(healthcare, record):
    claim = healthcare.claim("accepts_plan")
    t = convo("Yes, we take that plan.")
    # extractor claims TRUE but supplies NO evidence span
    ex = Extraction(claim_id="accepts_plan", answer_value=True, evidence_span=None,
                    source_role=SourceRole.FRONT_DESK)
    att = evaluate(ex, claim, record, t, healthcare)
    assert att.verdict == Verdict.UNCLEAR
    assert DiagnosticTag.AMBIGUOUS in att.diagnostic_tags


def test_non_verbatim_span_forces_unclear(healthcare, record):
    claim = healthcare.claim("accepts_plan")
    t = convo("Yes, we take that plan.")
    ex = Extraction(claim_id="accepts_plan", answer_value=True,
                    evidence_span="we happily accept Northline Health members",  # not in transcript
                    source_role=SourceRole.FRONT_DESK)
    att = evaluate(ex, claim, record, t, healthcare)
    assert att.verdict == Verdict.UNCLEAR
    assert att.evidence_span is None


def test_verbatim_span_resolves_match(healthcare, record):
    claim = healthcare.claim("accepts_plan")
    t = convo("Yes, we do accept Northline Health, always have.")
    ex = Extraction(claim_id="accepts_plan", answer_value=True,
                    evidence_span="we do accept Northline Health",
                    source_role=SourceRole.FRONT_DESK)
    att = evaluate(ex, claim, record, t, healthcare)
    assert att.verdict == Verdict.MATCH
    assert att.evidence_span == "we do accept Northline Health"


def test_verbatim_span_resolves_mismatch(healthcare, record):
    claim = healthcare.claim("accepts_plan")
    t = convo("No, we stopped taking Northline Health this year.")
    ex = Extraction(claim_id="accepts_plan", answer_value=False,
                    evidence_span="we stopped taking Northline Health this year",
                    source_role=SourceRole.FRONT_DESK)
    att = evaluate(ex, claim, record, t, healthcare)
    assert att.verdict == Verdict.MISMATCH


def test_conflicting_is_unclear(healthcare, record):
    claim = healthcare.claim("accepts_plan")
    t = convo("Yes we take it. Actually I'm not sure, we may have dropped it.")
    ex = Extraction(claim_id="accepts_plan", answer_value=True,
                    evidence_span="Yes we take it", conflicting=True,
                    source_role=SourceRole.FRONT_DESK)
    att = evaluate(ex, claim, record, t, healthcare)
    assert att.verdict == Verdict.UNCLEAR
    assert DiagnosticTag.CONFLICTING in att.diagnostic_tags


def test_no_contact_ignores_extraction(healthcare, record):
    claim = healthcare.claim("accepts_plan")
    t = Transcript(call_id="c1", outcome=CallOutcome.NO_CONTACT,
                   failure_code="no_answer", diagnostic_tag=DiagnosticTag.NO_ANSWER)
    ex = Extraction(claim_id="accepts_plan", answer_value=True,
                    evidence_span="fabricated", source_role=SourceRole.FRONT_DESK)
    att = evaluate(ex, claim, record, t, healthcare)
    assert att.verdict == Verdict.NO_CONTACT
    assert att.evidence_span is None


def test_expiry_is_pack_window(healthcare, record):
    claim = healthcare.claim("accepts_plan")
    t = convo("Yes, we accept Northline Health.")
    ex = Extraction(claim_id="accepts_plan", answer_value=True,
                    evidence_span="we accept Northline Health", source_role=SourceRole.FRONT_DESK)
    att = evaluate(ex, claim, record, t, healthcare)
    assert att.expires_at is not None
    delta = att.expires_at - att.attested_at
    assert abs(delta - timedelta(days=healthcare.expires_after_days)) < timedelta(seconds=2)


def test_invariant_guard_catches_bad_span(healthcare, record):
    """If evaluate() ever set a resolved verdict without a real span, this must raise."""
    from ghostline.models import Attestation
    from ghostline.verdict import _assert_invariant

    bad = Attestation(record_id="r1", claim_id="accepts_plan", pack_ref="healthcare@1",
                      verdict=Verdict.MATCH, evidence_span=None)
    with pytest.raises(VerdictError):
        _assert_invariant(bad, convo("anything"))
