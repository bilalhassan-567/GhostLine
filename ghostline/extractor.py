"""Extraction: pull one claim's answer + a MANDATORY verbatim evidence span from a transcript.

Two implementations:
  * HeuristicExtractor  — deterministic, no API key. Cue-word polarity over on-topic responder
                          turns. Used for CI, tests, and any no-LLM run (clearly labelled).
  * LLMExtractor        — the real extractor. Structured output; the returned span is
                          re-validated against the transcript in code — a span the model
                          invents is dropped to None, which forces UNCLEAR downstream.

Whatever the source, the evidence span is only ever trusted if it appears verbatim in a
responder turn. That check lives in `verdict.evaluate`, not here — this module just tries its
best and never fabricates.
"""

from __future__ import annotations

import json
import re
from typing import Protocol

from .config import Settings, get_settings
from .models import Claim, Extraction, Record, SourceRole, Transcript

_AFFIRM = re.compile(
    r"\b(yes|yeah|yep|we do|we accept|we take|we still (take|accept)|correct|that's right|"
    r"absolutely|of course|we are accepting|we're accepting)\b",
    re.IGNORECASE,
)
_DENY = re.compile(
    r"\b(no|nope|we don'?t|we do not|we stopped|we dropped|dropped|we no longer|not accepting|"
    r"we can'?t take|we're not taking|that'?s not|we moved|we relocated|waitlist only)\b",
    re.IGNORECASE,
)
_HEDGE = re.compile(
    r"\b(not sure|i think|maybe|might have|depends|couldn'?t tell|you'?d have to check|"
    r"i'?m not certain|let me not say|honestly couldn'?t|check your card|talk to)\b",
    re.IGNORECASE,
)

_ROLE_CUES: list[tuple[re.Pattern[str], SourceRole]] = [
    (re.compile(r"answering service|after[- ]hours service", re.IGNORECASE), SourceRole.ANSWERING_SERVICE),
    (re.compile(r"call center|call centre", re.IGNORECASE), SourceRole.CALL_CENTER),
    (re.compile(r"billing (department|office)|this is billing", re.IGNORECASE), SourceRole.BILLING_DEPT),
    (re.compile(r"front desk|reception", re.IGNORECASE), SourceRole.FRONT_DESK),
]


class Extractor(Protocol):
    name: str

    def extract(self, transcript: Transcript, claim: Claim, record: Record) -> Extraction: ...


# --------------------------------------------------------------------------------------
def _guess_role(transcript: Transcript) -> SourceRole:
    joined = " ".join(t.text for t in transcript.turns)
    for pat, role in _ROLE_CUES:
        if pat.search(joined):
            return role
    return SourceRole.FRONT_DESK if transcript.user_text else SourceRole.UNKNOWN


def _on_topic(text: str, claim: Claim, record: Record) -> bool:
    terms = [t.lower() for t in claim.subject_terms]
    if record.address:
        terms.append(record.address.lower())
    if not terms:
        return True
    low = text.lower()
    return any(term in low for term in terms)


class HeuristicExtractor:
    name = "heuristic"

    def extract(self, transcript: Transcript, claim: Claim, record: Record) -> Extraction:
        role = _guess_role(transcript)
        user_turns = [t.text.strip() for t in transcript.turns if t.speaker.value == "user"]
        on_topic = [t for t in user_turns if _on_topic(t, claim, record)]
        # Only fall back to every turn when the claim gave us nothing to filter on.
        topical = on_topic if (on_topic or claim.subject_terms) else user_turns

        polarities: list[tuple[bool, str]] = []
        hedged_on_topic = False
        for turn in topical:
            has_yes = bool(_AFFIRM.search(turn))
            has_no = bool(_DENY.search(turn))
            hedged = bool(_HEDGE.search(turn))
            if has_yes and not has_no:
                polarities.append((True, turn))
            elif has_no and not has_yes:
                polarities.append((False, turn))
            elif has_yes and has_no:
                polarities += [(True, turn), (False, turn)]
            elif hedged:
                hedged_on_topic = True

        distinct = {p for p, _ in polarities}

        if not distinct:
            return Extraction(
                claim_id=claim.claim_id, source_role=role,
                answer_value=None, evidence_span=None,
                answer_text=topical[0] if topical else "",
                reasoning="No on-topic responder statement resolved to yes or no.",
            )
        if len(distinct) == 2 or hedged_on_topic:
            return Extraction(
                claim_id=claim.claim_id, source_role=role, conflicting=True,
                answer_value=None, evidence_span=_tighten(polarities[0][1]),
                answer_text=" / ".join(dict.fromkeys(t for _, t in polarities)),
                reasoning="Responder gave a firm answer and then walked it back, or said both.",
            )
        value, turn = polarities[0]
        return Extraction(
            claim_id=claim.claim_id, source_role=role,
            answer_value=value, evidence_span=_tighten(turn), answer_text=turn,
            reasoning=f"Single consistent {'affirmative' if value else 'negative'} statement.",
        )


def _tighten(turn: str) -> str:
    """Prefer the clause carrying the yes/no over the whole run-on turn (still verbatim)."""
    for part in re.split(r"(?<=[.!?])\s+", turn):
        if _AFFIRM.search(part) or _DENY.search(part):
            return part.strip()
    return turn.strip()


# --------------------------------------------------------------------------------------
_LLM_SYSTEM = """You extract one fact from a phone-call transcript for a data-verification \
system. You must be conservative: if the responder did not clearly answer, say so. Never \
invent or paraphrase the evidence quote — it must be copied character-for-character from a \
single USER turn. If no such quote exists, return evidence_span = null and answer_value = null."""


class LLMExtractor:
    name = "llm"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        from anthropic import Anthropic

        self._client = Anthropic(api_key=self.settings.llm_api_key)

    def extract(self, transcript: Transcript, claim: Claim, record: Record) -> Extraction:
        convo = "\n".join(f"[{t.speaker.value}] {t.text}" for t in transcript.turns)
        prompt = (
            f"CLAIM: {claim.question.strip()}\n"
            f"HOW TO INTERPRET THE ANSWER: {claim.answer_guidance.strip()}\n"
            f"RECORD: {record.name}"
            + (f", {record.address}" if record.address else "")
            + f"\n\nTRANSCRIPT:\n{convo}\n\n"
            "Return JSON with keys: answer_value (true|false|null for a yes/no claim), "
            "answer_text (the responder's answer in their own words, may paraphrase), "
            "evidence_span (a verbatim substring of ONE user turn that proves the answer, or "
            "null), source_role (front_desk|answering_service|call_center|billing_dept|"
            "voicemail|ivr_only|unknown), conflicting (true if the responder contradicted "
            "themselves), reasoning (one sentence)."
        )
        msg = self._client.messages.create(
            model=self.settings.llm_model,
            max_tokens=600,
            system=_LLM_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        data = _loads_json(raw)

        span = data.get("evidence_span")
        if span and not transcript.contains_verbatim(span):
            # The model produced a quote that is not actually in the transcript. Drop it.
            span = None
            data["reasoning"] = (data.get("reasoning") or "") + " [span rejected: not verbatim]"

        role = data.get("source_role") or "unknown"
        try:
            role_enum = SourceRole(role)
        except ValueError:
            role_enum = SourceRole.UNKNOWN

        return Extraction(
            claim_id=claim.claim_id,
            answer_value=data.get("answer_value"),
            answer_text=data.get("answer_text") or "",
            evidence_span=span,
            source_role=role_enum,
            conflicting=bool(data.get("conflicting")),
            reasoning=data.get("reasoning") or "",
        )


def _loads_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.IGNORECASE | re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group(0)) if m else {}


# --------------------------------------------------------------------------------------
def get_extractor(settings: Settings | None = None) -> Extractor:
    settings = settings or get_settings()
    if settings.has_llm:
        try:
            return LLMExtractor(settings)
        except Exception as exc:  # noqa: BLE001 - fall back rather than crash a run
            print(f"[ghostline] LLM extractor unavailable ({exc!s}); using heuristic extractor")
    return HeuristicExtractor()
