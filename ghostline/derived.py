"""Derived calls (master doc §4.10) - "the answer wrote the next call".

When a transcript surfaces a lead - a new contact person, a move, a different number - propose
a follow-up verification. The proposal is never placed automatically: it requires one explicit
human approval, then re-enters the Policy Gate exactly like any other call.

Security invariant (RULES.md §5): a phone number found *inside a transcript* is data, not a
dial target. `DerivedProposal.phone` is only ever populated as a *suggestion* a human must
approve; the default derived call re-dials the number already on the record.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Transcript

# "Sarah handles that now", "you'll want to talk to Dr. Chen", "ask for the office manager"
_NEW_CONTACT = re.compile(
    r"\b(?:talk to|ask for|speak (?:to|with)|that'?s|contact|reach out to|handled by)\s+"
    r"(?:dr\.?\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
)
_MOVED = re.compile(
    r"\b(?:we(?:'ve| have)? moved|we relocated|we'?re now (?:at|on|in)|new (?:address|location) is)\b"
    r"[^.]{0,60}",
    re.IGNORECASE,
)
_OTHER_NUMBER = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
_FILLER_NAMES = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Today", "Tomorrow"}


@dataclass
class DerivedProposal:
    kind: str          # "contact" | "moved" | "number"
    detail: str        # the phrase that triggered it
    reason: str        # human-readable "why we propose this"
    phone: str | None = None   # suggested number, ONLY when the transcript named one
    goal_hint: str | None = None  # extra instruction for the follow-up call


def detect(transcript: Transcript) -> DerivedProposal | None:
    text = " ".join(t.text for t in transcript.turns if t.speaker.value == "user")

    m = _OTHER_NUMBER.search(text)
    if m and sum(c.isdigit() for c in m.group(1)) >= 10:
        digits = "+" + re.sub(r"\D", "", m.group(1)).lstrip("+")
        return DerivedProposal(
            kind="number",
            detail=m.group(1).strip(),
            reason=f"The person referred you to another number ({m.group(1).strip()}). "
            "Ghostline will not dial it automatically - approve to verify it as a new record.",
            phone=digits,
        )

    m = _MOVED.search(text)
    if m:
        return DerivedProposal(
            kind="moved",
            detail=m.group(0).strip(),
            reason="The office indicated it has moved. Re-verify the address claim on a "
            "follow-up call to the same number.",
            goal_hint="Confirm the current street address and whether the old address still reaches this office.",
        )

    for m in _NEW_CONTACT.finditer(text):
        name = m.group(1).strip()
        if name in _FILLER_NAMES or len(name) < 3:
            continue
        return DerivedProposal(
            kind="contact",
            detail=name,
            reason=f"A different contact was named ({name}). Re-verify on a follow-up call to "
            f"the same number, asking for {name}.",
            goal_hint=f"Ask to speak with {name}, then re-ask the same questions.",
        )
    return None
