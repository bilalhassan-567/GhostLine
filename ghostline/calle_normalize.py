"""Turn a raw CALL-E CallTask payload into Ghostline's internal `Transcript`.

Both the live call engine and the replay harness go through here, so downstream code never
sees a raw SDK/API dict — only a normalized `Transcript`. See
`Docs/research/CALL_E_INTEGRATION.md` for the CallTask shape (transcript lives at
recipients[].attempts[].transcript_turns[]).
"""

from __future__ import annotations

from datetime import datetime

from .models import (
    CallOutcome,
    DiagnosticTag,
    Speaker,
    Transcript,
    TranscriptTurn,
)

# Best-effort mapping of CALL-E failure strings -> our diagnostic tags. The one-shot Calls API
# does not enumerate failure_code (only the Goal path does), so these are refined from the
# first real calls (Day 1) — see CALL_E_FEEDBACK.md.
_FAILURE_TAGS: dict[str, DiagnosticTag] = {
    "no_answer": DiagnosticTag.NO_ANSWER,
    "no-answer": DiagnosticTag.NO_ANSWER,
    "noanswer": DiagnosticTag.NO_ANSWER,
    "no_human_answered": DiagnosticTag.NO_ANSWER,
    "voicemail": DiagnosticTag.VOICEMAIL,
    "voice_mail": DiagnosticTag.VOICEMAIL,
    "answering_machine": DiagnosticTag.VOICEMAIL,
    "ivr": DiagnosticTag.IVR,
    "ivr_only": DiagnosticTag.IVR,
    "menu": DiagnosticTag.IVR,
    "busy": DiagnosticTag.BUSY,
    "declined": DiagnosticTag.DECLINED,
    "invalid_phone": DiagnosticTag.INVALID_NUMBER,
    "invalid_number": DiagnosticTag.INVALID_NUMBER,
    "invalid_recipient": DiagnosticTag.INVALID_NUMBER,
    "unsupported_region": DiagnosticTag.UNSUPPORTED_REGION,
    "unsupported_language": DiagnosticTag.UNSUPPORTED_REGION,
    "recipient_blocked": DiagnosticTag.BLOCKED,
    "policy_violation": DiagnosticTag.BLOCKED,
}

_TERMINAL_OK = {"completed"}
_TERMINAL_BAD = {"failed", "canceled", "cancelled"}


def _parse_dt(value: object) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _pick_attempt(recipient: dict) -> dict | None:
    attempts = recipient.get("attempts") or []
    if not attempts:
        return None
    for a in reversed(attempts):
        if a.get("status") == "completed" and a.get("transcript_turns"):
            return a
    return attempts[-1]


def _tag_for_failure(code: str | None) -> DiagnosticTag:
    if not code:
        return DiagnosticTag.CALL_FAILED
    return _FAILURE_TAGS.get(code.strip().lower(), DiagnosticTag.CALL_FAILED)


def transcript_from_calltask(call: dict) -> Transcript:
    status = (call.get("status") or "").lower()
    recipients = call.get("recipients") or []
    recipient = recipients[0] if recipients else {}
    attempt = _pick_attempt(recipient) or {}

    turns = [
        TranscriptTurn(
            offset_seconds=t.get("offset_seconds"),
            speaker=_speaker(t.get("speaker")),
            text=t.get("text") or "",
        )
        for t in (attempt.get("transcript_turns") or [])
    ]
    has_user_speech = any(t.speaker == Speaker.USER and t.text.strip() for t in turns)

    conf = call.get("completion_confidence") or {}
    common = {
        "call_id": call.get("id"),
        "provider_call_id": attempt.get("provider_call_id"),
        "turns": turns,
        "started_at": _parse_dt(attempt.get("started_at") or call.get("created_at")),
        "completed_at": _parse_dt(attempt.get("completed_at") or call.get("completed_at")),
        "calle_structured_result": call.get("structured_result")
        or recipient.get("structured_result"),
        "calle_confidence_label": conf.get("label"),
        "calle_confidence_score": conf.get("score"),
        "calle_task_completed": call.get("task_completed"),
    }

    failure_code = (
        call.get("failure_code")
        or attempt.get("failure_code")
        or recipient.get("failure_code")
    )
    failure_message = call.get("failure_message") or attempt.get("failure_message")

    # Terminal failure, or "completed" but nobody actually spoke (voicemail / IVR / dead air).
    if status in _TERMINAL_BAD or (status in _TERMINAL_OK and not has_user_speech):
        tag = _tag_for_failure(failure_code)
        if tag == DiagnosticTag.CALL_FAILED and status in _TERMINAL_OK:
            # Completed with only bot/IVR turns and no failure_code: infer from content.
            tag = _infer_no_speech_tag(turns)
        return Transcript(
            outcome=CallOutcome.NO_CONTACT,
            failure_code=failure_code or ("no_user_speech" if status in _TERMINAL_OK else status),
            failure_message=failure_message,
            diagnostic_tag=tag,
            **common,
        )

    if status not in _TERMINAL_OK:
        # queued / in_progress — not terminal yet. Caller should keep polling.
        return Transcript(outcome=CallOutcome.ERROR, failure_code=status or "not_terminal", **common)

    return Transcript(outcome=CallOutcome.CONVERSATION, **common)


def _speaker(raw: object) -> Speaker:
    try:
        return Speaker(str(raw).lower())
    except ValueError:
        return Speaker.UNKNOWN


def _infer_no_speech_tag(turns: list[TranscriptTurn]) -> DiagnosticTag:
    joined = " ".join(t.text.lower() for t in turns)
    if any(k in joined for k in ("press ", "for english", "main menu", "dial ", "extension")):
        return DiagnosticTag.IVR
    if any(k in joined for k in ("leave a message", "voicemail", "after the tone", "not available")):
        return DiagnosticTag.VOICEMAIL
    return DiagnosticTag.NO_ANSWER
