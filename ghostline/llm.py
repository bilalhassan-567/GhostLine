"""One text-completion call, provider-agnostic.

Both LLM call sites (the transcript extractor and the claim-pack generator) go through
`complete(system, prompt)`. Provider is chosen from the environment:

  * GEMINI_API_KEY  -> Google Gemini (free tier, no card) via the REST API, no extra dep
  * LLM_API_KEY / ANTHROPIC_API_KEY -> Anthropic (uses the `anthropic` SDK)

If neither is set, `complete()` raises and callers fall back to their deterministic path.
"""

from __future__ import annotations

import httpx

from .config import Settings, get_settings

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class NoLLMConfigured(RuntimeError):
    pass


def provider(settings: Settings | None = None) -> str | None:
    s = settings or get_settings()
    if s.gemini_api_key:
        return "gemini"
    if s.llm_api_key:
        return "anthropic"
    return None


def complete(system: str, prompt: str, *, settings: Settings | None = None, max_tokens: int = 900) -> str:
    s = settings or get_settings()
    p = provider(s)
    if p == "gemini":
        return _gemini(system, prompt, s, max_tokens)
    if p == "anthropic":
        return _anthropic(system, prompt, s, max_tokens)
    raise NoLLMConfigured("set GEMINI_API_KEY (free) or LLM_API_KEY")


def _gemini(system: str, prompt: str, s: Settings, max_tokens: int) -> str:
    url = f"{GEMINI_BASE}/models/{s.gemini_model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": max_tokens,
            # Both call sites want a JSON object back.
            "responseMimeType": "application/json",
        },
    }
    r = httpx.post(url, params={"key": s.gemini_api_key}, json=body, timeout=45)
    r.raise_for_status()
    data = r.json()
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(part.get("text", "") for part in parts)


def _anthropic(system: str, prompt: str, s: Settings, max_tokens: int) -> str:
    from anthropic import Anthropic

    msg = Anthropic(api_key=s.llm_api_key).messages.create(
        model=s.llm_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
