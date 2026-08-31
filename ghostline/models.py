"""Core domain objects for Ghostline.

These are domain-neutral on purpose. Healthcare is the flagship *evidence* case, not the
product's identity — nothing here hardcodes it. A new domain is a new claim pack (a YAML
config), never a change to these types.

Lifecycle: asserted -> verified -> evidenced -> corrected -> expired -> re-verified.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------------------
# Verdicts
# --------------------------------------------------------------------------------------
class Verdict(str, enum.Enum):
    """The four — and only four — user-facing outcomes."""

    MATCH = "MATCH"          # evidence supports the claim
    MISMATCH = "MISMATCH"    # evidence contradicts the claim
    UNCLEAR = "UNCLEAR"      # information came back, but not enough to make a binary call
    NO_CONTACT = "NO_CONTACT"  # no usable conversation happened

    @property
    def is_resolved(self) -> bool:
        """True when a real answer was obtained (MATCH or MISMATCH)."""
        return self in (Verdict.MATCH, Verdict.MISMATCH)


class DiagnosticTag(str, enum.Enum):
    """Internal-only detail. Never surfaced as a primary UI state; used for the failure
    taxonomy and the reliability benchmark."""

    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTING = "CONFLICTING"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    IVR = "IVR"
    VOICEMAIL = "VOICEMAIL"
    BUSY = "BUSY"
    NO_ANSWER = "NO_ANSWER"
    CALL_FAILED = "CALL_FAILED"
    INVALID_NUMBER = "INVALID_NUMBER"
    UNSUPPORTED_REGION = "UNSUPPORTED_REGION"  # CALL-E APIError: unsupported_region / _language
    BLOCKED = "BLOCKED"                        # recipient_blocked / policy_violation
    DECLINED = "DECLINED"                      # responder refused to answer


class SourceRole(str, enum.Enum):
    """Who answered the phone. Caps the confidence an attestation can reach."""

    FRONT_DESK = "front_desk"
    BILLING_DEPT = "billing_dept"
    CALL_CENTER = "call_center"
    ANSWERING_SERVICE = "answering_service"
    VOICEMAIL = "voicemail"
    IVR_ONLY = "ivr_only"
    UNKNOWN = "unknown"

    @property
    def confidence_ceiling(self) -> Confidence:
        return {
            SourceRole.FRONT_DESK: Confidence.HIGH,
            SourceRole.BILLING_DEPT: Confidence.HIGH,
            SourceRole.CALL_CENTER: Confidence.MEDIUM,
            SourceRole.ANSWERING_SERVICE: Confidence.MEDIUM,
            SourceRole.VOICEMAIL: Confidence.LOW,
            SourceRole.IVR_ONLY: Confidence.LOW,
            SourceRole.UNKNOWN: Confidence.MEDIUM,
        }[self]


class Confidence(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def capped_at(self, ceiling: Confidence) -> Confidence:
        order = [Confidence.LOW, Confidence.MEDIUM, Confidence.HIGH]
        return order[min(order.index(self), order.index(ceiling))]


# --------------------------------------------------------------------------------------
# Claim packs
# --------------------------------------------------------------------------------------
class ExpectedType(str, enum.Enum):
    BOOLEAN = "boolean"
    STRING = "string"
    ENUM = "enum"


class Claim(BaseModel):
    """A single testable statement about a record."""

    claim_id: str
    question: str                       # what the agent asks on the call
    expected_type: ExpectedType = ExpectedType.BOOLEAN
    enum_values: list[str] = Field(default_factory=list)  # when expected_type == ENUM
    # Human-readable description of what each answer means, handed to the extractor.
    answer_guidance: str = ""
    # Phrases that mark a transcript turn as being *about* this claim. Used by the
    # deterministic (no-LLM) extractor to stay on-topic; the LLM extractor ignores these.
    subject_terms: list[str] = Field(default_factory=list)

    @field_validator("enum_values")
    @classmethod
    def _enum_needs_values(cls, v: list[str], info) -> list[str]:
        if info.data.get("expected_type") == ExpectedType.ENUM and not v:
            raise ValueError(f"claim {info.data.get('claim_id')!r}: enum claim needs enum_values")
        return v


class ClaimPack(BaseModel):
    """A reusable, domain-specific bundle of claims. The engine's only extension point.

    Fork Ghostline for a new domain == write one of these. Nothing else changes.
    """

    pack_id: str
    version: int = 1
    display_name: str
    description: str = ""
    # How long an attestation from this pack stays valid before re-verification.
    expires_after_days: int = 90
    # Prepended to every call goal — disclosure, tone, guardrails.
    call_preamble: str = (
        "You are an automated verification call. Disclose at the start that this is an "
        "automated call and that no personal or account information is being requested. "
        "Keep the call under 90 seconds and ask only the questions listed."
    )
    claims: list[Claim]

    @property
    def ref(self) -> str:
        return f"{self.pack_id}@{self.version}"

    def claim(self, claim_id: str) -> Claim:
        for c in self.claims:
            if c.claim_id == claim_id:
                return c
        raise KeyError(f"no claim {claim_id!r} in pack {self.ref}")


# --------------------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------------------
class Record(BaseModel):
    """One row of an input dataset. Same shape whether it arrived by CSV or the manual form."""

    record_id: str
    name: str
    phone: str                          # validated to E.164 by the policy gate, not here
    address: str = ""
    region: str | None = None           # ISO country code hint for CALL-E routing, e.g. "US"
    locale: str | None = None           # BCP-47 hint, e.g. "en-US"
    # claim_id -> asserted value we are checking against
    claims: dict[str, object] = Field(default_factory=dict)


# --------------------------------------------------------------------------------------
# Transcript (normalized from a CALL-E call result)
# --------------------------------------------------------------------------------------
class Speaker(str, enum.Enum):
    BOT = "bot"
    USER = "user"
    UNKNOWN = "unknown"


class TranscriptTurn(BaseModel):
    offset_seconds: int | None = None
    speaker: Speaker
    text: str


class CallOutcome(str, enum.Enum):
    """What the call engine could establish about the call itself, before any extraction."""

    CONVERSATION = "conversation"   # a human conversation happened; transcript is usable
    NO_CONTACT = "no_contact"       # voicemail / IVR / no-answer / failed / blocked
    ERROR = "error"                 # our side failed (config, budget) — not a verdict


class Transcript(BaseModel):
    """Everything downstream of the call engine sees only this — never the raw SDK payload."""

    call_id: str | None = None
    provider_call_id: str | None = None
    outcome: CallOutcome
    turns: list[TranscriptTurn] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    # CALL-E's own read, kept as a secondary signal (never authoritative). See master doc A4.
    calle_structured_result: dict[str, object] | None = None
    calle_confidence_label: str | None = None
    calle_confidence_score: float | None = None
    calle_task_completed: bool | None = None
    # Populated on NO_CONTACT / ERROR.
    failure_code: str | None = None
    failure_message: str | None = None
    diagnostic_tag: DiagnosticTag | None = None

    @property
    def user_text(self) -> str:
        """All the responder's turns, joined — the only text the extractor may quote from."""
        return " ".join(t.text.strip() for t in self.turns if t.speaker == Speaker.USER)

    def contains_verbatim(self, span: str) -> bool:
        """A span is valid only if it appears verbatim in a responder turn (whitespace- and
        case-insensitive). This is what the evidence-span-or-abstain rule checks against."""
        if not span or not span.strip():
            return False
        needle = _normalize(span)
        return any(needle in _normalize(t.text) for t in self.turns if t.speaker == Speaker.USER)


def _normalize(s: str) -> str:
    return " ".join(s.lower().split())


# --------------------------------------------------------------------------------------
# Extraction (extractor output -> verdict input)
# --------------------------------------------------------------------------------------
class Extraction(BaseModel):
    """What the extractor pulled from the transcript for one claim. The extractor is REQUIRED
    to return evidence_span=None rather than inventing one — the verdict evaluator turns a
    missing span into UNCLEAR, in code."""

    claim_id: str
    answer_value: object | None = None      # normalized: bool | str | None
    answer_text: str = ""                   # the responder's own words, paraphrase allowed here
    evidence_span: str | None = None        # MUST be verbatim from a responder turn, or None
    source_role: SourceRole = SourceRole.UNKNOWN
    reasoning: str = ""
    conflicting: bool = False               # responder said contradictory things


# --------------------------------------------------------------------------------------
# Attestation (the output of one resolved claim)
# --------------------------------------------------------------------------------------
class Attestation(BaseModel):
    record_id: str
    claim_id: str
    pack_ref: str
    verdict: Verdict
    asserted_value: object | None = None
    answer_text: str = ""
    evidence_span: str | None = None
    source_role: SourceRole = SourceRole.UNKNOWN
    confidence: Confidence = Confidence.LOW
    diagnostic_tags: list[DiagnosticTag] = Field(default_factory=list)
    evaluation_reason: str = ""
    call_id: str | None = None
    provider_call_id: str | None = None
    attested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    # Secondary signal — CALL-E's own read, never used to decide the verdict.
    calle_structured_result: dict[str, object] | None = None
    calle_confidence_label: str | None = None
    calle_task_completed: bool | None = None

    def set_expiry(self, days: int) -> None:
        self.expires_at = self.attested_at + timedelta(days=days)

    @property
    def is_correction(self) -> bool:
        """Only evidence-backed MISMATCH rows populate the corrections file. An UNCLEAR record
        never silently becomes a correction."""
        return self.verdict == Verdict.MISMATCH and bool(self.evidence_span)
