"""Draft a claim pack from a plain-English request (master doc §4.12a).

The generated pack is a *proposal*. Nothing calls anyone until a human approves the
questions - same rule as derived calls. When an LLM key is present it drafts the claims;
otherwise a deterministic template turns the sentence into a single best-effort claim so the
flow still works offline.
"""

from __future__ import annotations

import json
import re

from .config import Settings, get_settings
from .models import Claim, ClaimPack, ExpectedType

_RECHECK_HINTS = [
    (re.compile(r"\bopen\b|\bhours\b|\bstill (there|around|operating)\b", re.IGNORECASE), 30),
    (re.compile(r"\baccept|\bplan\b|\bcover|\binsurance\b|\bin-network\b", re.IGNORECASE), 90),
    (re.compile(r"\baddress|\blocation|\bmoved\b|\bcontact\b|\bsupplier\b", re.IGNORECASE), 180),
]


def _suggest_recheck_days(text: str) -> int:
    for pat, days in _RECHECK_HINTS:
        if pat.search(text):
            return days
    return 90


_SYSTEM = (
    "You design claim packs for a phone-verification system. A claim pack is a short list of "
    "yes/no questions to ask a business over the phone, each with strict guidance on what "
    "counts as a definite yes or no. Be conservative: vague answers must map to 'unknown'."
)


def _llm_pack(prompt: str, settings: Settings) -> dict:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.llm_api_key)
    msg = client.messages.create(
        model=settings.llm_model,
        max_tokens=900,
        system=_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Request: {prompt.strip()}\n\n"
                    "Return JSON: {display_name, expires_after_days, call_preamble, "
                    "claims:[{claim_id (snake_case), question, answer_guidance, "
                    "subject_terms:[lowercase phrases that mark a turn as on-topic]}]}. "
                    "2-4 claims. Each question names its own subject so the answer is "
                    "unambiguous. answer_guidance must reject non-specific answers."
                ),
            }
        ],
    )
    raw = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.IGNORECASE | re.MULTILINE).strip()
    return json.loads(raw)


def _template_pack(prompt: str) -> dict:
    subject = re.sub(r"^(verify|check|confirm|call and (ask|check)|find out)\s+", "", prompt.strip(), flags=re.IGNORECASE)
    subject = subject.rstrip(". ")
    return {
        "display_name": subject[:60].capitalize() or "Custom verification",
        "expires_after_days": _suggest_recheck_days(prompt),
        "claims": [
            {
                "claim_id": "primary_claim",
                "question": f"{subject[0].upper() + subject[1:]}?" if subject else "Is this still accurate?",
                "answer_guidance": (
                    "yes only on an explicit confirmation of the exact thing asked. no only on "
                    "an explicit denial. Anything hedged, deferred, or about something adjacent "
                    "is unknown."
                ),
                "subject_terms": [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", subject)][:6],
            }
        ],
        "_generator": "template (no LLM key set)",
    }


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:40] or "custom"


def draft_pack(prompt: str, settings: Settings | None = None) -> ClaimPack:
    settings = settings or get_settings()
    try:
        raw = _llm_pack(prompt, settings) if settings.has_llm else _template_pack(prompt)
    except Exception:  # noqa: BLE001 - never fail the flow; fall back to the template
        raw = _template_pack(prompt)

    raw.setdefault("expires_after_days", _suggest_recheck_days(prompt))
    raw.setdefault("pack_id", _slug(raw.get("display_name", "custom")))
    raw.setdefault("version", 1)
    claims = []
    for i, c in enumerate(raw.get("claims", []), 1):
        claims.append(
            Claim(
                claim_id=c.get("claim_id") or f"claim_{i}",
                question=c["question"],
                expected_type=ExpectedType.BOOLEAN,
                answer_guidance=c.get("answer_guidance", ""),
                subject_terms=[str(t).lower() for t in c.get("subject_terms", [])],
            )
        )
    raw["claims"] = claims
    if "call_preamble" not in raw:
        raw.pop("call_preamble", None)
    return ClaimPack.model_validate({k: v for k, v in raw.items() if not k.startswith("_")})
