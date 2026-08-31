"""The verification pipeline, from a normalized transcript to a written attestation.

    transcript --(extractor)--> Extraction --(verdict.evaluate)--> Attestation

This is the seam the replay harness and the live call engine both feed. Neither knows nor
cares whether the transcript came from a fixture or a real CALL-E call.
"""

from __future__ import annotations

from .extractor import Extractor, get_extractor
from .models import Attestation, CallOutcome, Claim, ClaimPack, Record, Transcript
from .verdict import evaluate


def resolve_claim(
    record: Record,
    claim: Claim,
    pack: ClaimPack,
    transcript: Transcript,
    extractor: Extractor | None = None,
) -> Attestation:
    extractor = extractor or get_extractor()

    if transcript.outcome != CallOutcome.CONVERSATION:
        # No conversation -> extraction is meaningless; evaluate() will return NO_CONTACT.
        from .models import Extraction

        return evaluate(Extraction(claim_id=claim.claim_id), claim, record, transcript, pack)

    extraction = extractor.extract(transcript, claim, record)
    return evaluate(extraction, claim, record, transcript, pack)


def resolve_record(
    record: Record,
    pack: ClaimPack,
    transcript: Transcript,
    extractor: Extractor | None = None,
) -> list[Attestation]:
    """Resolve every claim the record asserts (or every claim in the pack if it asserts none)."""
    extractor = extractor or get_extractor()
    claim_ids = list(record.claims) or [c.claim_id for c in pack.claims]
    return [
        resolve_claim(record, pack.claim(cid), pack, transcript, extractor) for cid in claim_ids
    ]
