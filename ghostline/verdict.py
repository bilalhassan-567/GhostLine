"""The verdict evaluator — the single most important file in the project.

The non-negotiable rule (master doc §4.4): a MATCH or MISMATCH verdict CANNOT be produced
unless there is a verbatim quoted span from a responder turn that supports it. No span ->
UNCLEAR. This is enforced here, in code, not in a README.

`evaluate()` is a pure function: (extraction, claim, record, transcript, pack) -> Attestation.
"""

from __future__ import annotations

from .models import (
    Attestation,
    CallOutcome,
    Claim,
    ClaimPack,
    Confidence,
    DiagnosticTag,
    ExpectedType,
    Extraction,
    Record,
    Transcript,
    Verdict,
)

_TRUE = {"true", "t", "yes", "y", "1", "accepts", "accepting", "confirmed"}
_FALSE = {"false", "f", "no", "n", "0", "denies", "declined", "not accepting"}


def normalize_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in _TRUE:
        return True
    if s in _FALSE:
        return False
    return None


def _normalize_answer(value: object, claim: Claim) -> object | None:
    if value is None:
        return None
    if claim.expected_type == ExpectedType.BOOLEAN:
        return normalize_bool(value)
    if claim.expected_type == ExpectedType.ENUM:
        s = str(value).strip().lower()
        for allowed in claim.enum_values:
            if s == allowed.strip().lower():
                return allowed
        return None
    return str(value).strip()


class VerdictError(RuntimeError):
    """Raised only if the evaluator's own output violates the evidence-span invariant — a bug
    guard, never expected to fire in normal operation."""


def evaluate(
    extraction: Extraction,
    claim: Claim,
    record: Record,
    transcript: Transcript,
    pack: ClaimPack,
) -> Attestation:
    att = Attestation(
        record_id=record.record_id,
        claim_id=claim.claim_id,
        pack_ref=pack.ref,
        verdict=Verdict.UNCLEAR,  # default; only positive evidence moves it
        asserted_value=record.claims.get(claim.claim_id),
        answer_text=extraction.answer_text,
        source_role=extraction.source_role,
        call_id=transcript.call_id,
        provider_call_id=transcript.provider_call_id,
        calle_structured_result=transcript.calle_structured_result,
        calle_confidence_label=transcript.calle_confidence_label,
        calle_task_completed=transcript.calle_task_completed,
    )
    att.set_expiry(pack.expires_after_days)

    # 1. No usable conversation -> NO_CONTACT. Extraction is irrelevant.
    if transcript.outcome != CallOutcome.CONVERSATION:
        att.verdict = Verdict.NO_CONTACT
        if transcript.diagnostic_tag:
            att.diagnostic_tags.append(transcript.diagnostic_tag)
        att.evaluation_reason = (
            transcript.failure_message
            or f"No usable conversation ({transcript.failure_code or 'unknown'})."
        )
        att.confidence = Confidence.LOW
        return att

    span = (extraction.evidence_span or "").strip()

    # 2. THE HARD RULE. A verbatim span is mandatory for any resolved verdict.
    if not span or not transcript.contains_verbatim(span):
        att.verdict = Verdict.UNCLEAR
        att.evidence_span = None
        att.diagnostic_tags.append(DiagnosticTag.AMBIGUOUS)
        att.evaluation_reason = (
            "No verbatim evidence span from the responder supports a call on this claim; "
            "abstaining rather than guessing."
            if not span
            else f"Proposed evidence span was not found verbatim in the transcript: {span!r}."
        )
        att.confidence = Confidence.LOW
        _assert_invariant(att, transcript)
        return att

    att.evidence_span = span

    # 3. Contradictory statements -> UNCLEAR (a real answer, but not a reliable one).
    if extraction.conflicting:
        att.verdict = Verdict.UNCLEAR
        att.diagnostic_tags.append(DiagnosticTag.CONFLICTING)
        att.evaluation_reason = "Responder gave contradictory answers; cannot resolve to a binary verdict."
        att.confidence = Confidence.LOW
        _assert_invariant(att, transcript)
        return att

    answer = _normalize_answer(extraction.answer_value, claim)
    asserted = (
        normalize_bool(att.asserted_value)
        if claim.expected_type == ExpectedType.BOOLEAN
        else att.asserted_value
    )

    # 4. We have a span but no usable answer value -> still UNCLEAR.
    if answer is None:
        att.verdict = Verdict.UNCLEAR
        att.diagnostic_tags.append(DiagnosticTag.LOW_CONFIDENCE)
        att.evaluation_reason = (
            f"Evidence span present ({span!r}) but it does not yield a definite answer to the claim."
        )
        att.confidence = Confidence.LOW
        _assert_invariant(att, transcript)
        return att

    # 5. Resolve.
    ceiling = extraction.source_role.confidence_ceiling
    if answer == asserted:
        att.verdict = Verdict.MATCH
        att.evaluation_reason = (
            f"Responder's statement ({span!r}) agrees with the asserted value ({asserted!r})."
        )
    else:
        att.verdict = Verdict.MISMATCH
        att.evaluation_reason = (
            f"Responder's statement ({span!r}) contradicts the asserted value "
            f"({asserted!r}); observed {answer!r}."
        )
    att.confidence = Confidence.MEDIUM.capped_at(ceiling)
    _assert_invariant(att, transcript)
    return att


def _assert_invariant(att: Attestation, transcript: Transcript) -> None:
    """Belt-and-braces: a resolved verdict MUST carry a verbatim span. If this ever fires it
    is a bug in `evaluate`, not bad input."""
    if att.verdict.is_resolved and (
        not att.evidence_span or not transcript.contains_verbatim(att.evidence_span)
    ):
        raise VerdictError(
            f"invariant violated: {att.verdict} produced without a verbatim evidence span "
            f"(record={att.record_id}, claim={att.claim_id})"
        )
