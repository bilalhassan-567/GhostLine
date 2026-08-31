"""The live call engine — the only place that actually spends a CALL-E call.

    plan (from PolicyGate) --> client.calls.create --> poll --> normalized Transcript

Every path returns a Transcript with a terminal `outcome`; nothing raises past here except a
genuine programming error. CALL-E API errors become NO_CONTACT / ERROR transcripts with a
diagnostic tag (see Docs/research/CALL_E_INTEGRATION.md §6).
"""

from __future__ import annotations

from .calle_normalize import _tag_for_failure, transcript_from_calltask
from .config import Settings, get_settings
from .models import CallOutcome, DiagnosticTag, Transcript
from .policy_gate import CallPlan

# CALL-E APIError.code values that mean "no call happened" vs "our fault / transient".
_NO_CONTACT_CODES = {
    "invalid_phone": DiagnosticTag.INVALID_NUMBER,
    "invalid_recipient": DiagnosticTag.INVALID_NUMBER,
    "no_recipients": DiagnosticTag.INVALID_NUMBER,
    "unsupported_region": DiagnosticTag.UNSUPPORTED_REGION,
    "unsupported_language": DiagnosticTag.UNSUPPORTED_REGION,
    "recipient_blocked": DiagnosticTag.BLOCKED,
    "policy_violation": DiagnosticTag.BLOCKED,
}
class CallEngine:
    def __init__(self, settings: Settings | None = None, client=None) -> None:
        self.settings = settings or get_settings()
        self._client = client  # inject for tests; created lazily otherwise

    @property
    def client(self):
        if self._client is None:
            from calle import CalleClient

            if not self.settings.calle_api_key:
                raise RuntimeError("CALLE_API_KEY is not set; cannot place live calls.")
            self._client = CalleClient(
                api_key=self.settings.calle_api_key, base_url=self.settings.calle_base_url
            )
        return self._client

    def dispatch(self, plan: CallPlan, *, webhook_url: str, metadata: dict) -> str:
        """Place a call and return immediately; CALL-E posts the terminal result to
        `webhook_url`. Used on serverless where we cannot poll on a background thread."""
        created = self.client.calls.create(
            task=plan.task,
            recipients=[{"phones": [plan.dial_e164], "region": plan.region, "locale": plan.locale}],
            result_schema=plan.result_schema,
            metadata={"record_id": plan.record_id, "ghostline": "1", **metadata},
            webhook_url=webhook_url,
            idempotency_key=plan.idempotency_key,
        )
        return str(created.get("id", ""))

    def place(self, plan: CallPlan) -> Transcript:
        """Place one call for an authorized plan and return a normalized Transcript."""
        from calle.errors import CalleAPIError, CalleConnectionError, CalleTimeoutError

        try:
            created = self.client.calls.create(
                task=plan.task,
                recipients=[
                    {
                        "phones": [plan.dial_e164],
                        "region": plan.region,
                        "locale": plan.locale,
                    }
                ],
                result_schema=plan.result_schema,
                metadata={"record_id": plan.record_id, "ghostline": "1"},
                idempotency_key=plan.idempotency_key,
            )
        except CalleAPIError as exc:
            return self._from_api_error(exc, plan)
        except (CalleConnectionError, CalleTimeoutError) as exc:
            return Transcript(
                outcome=CallOutcome.ERROR,
                failure_code="connection",
                failure_message=str(exc),
                diagnostic_tag=DiagnosticTag.CALL_FAILED,
            )

        call_id = str(created.get("id", ""))
        try:
            final = self.client.calls.wait_for_result(
                call_id,
                interval_seconds=self.settings.call_poll_interval_s,
                timeout_seconds=self.settings.call_timeout_s,
            )
        except CalleTimeoutError:
            # No cancel endpoint exists (master doc A6): we stop waiting; the call still runs.
            final = self.client.calls.get(call_id)

        return transcript_from_calltask(final)

    def _from_api_error(self, exc, plan: CallPlan) -> Transcript:
        code = getattr(exc, "code", None) or "api_error"
        if code in _NO_CONTACT_CODES:
            return Transcript(
                outcome=CallOutcome.NO_CONTACT,
                failure_code=code,
                failure_message=str(exc),
                diagnostic_tag=_NO_CONTACT_CODES[code],
            )
        return Transcript(
            outcome=CallOutcome.ERROR,
            failure_code=code,
            failure_message=str(exc),
            diagnostic_tag=_tag_for_failure(code),
        )
