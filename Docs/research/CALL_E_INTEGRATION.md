# GHOSTLINE — CALL-E Integration Reference

**Verified against:** `calle-ai` SDK **v0.7.0** (import module `calle`) + CALL-E Developer API
**OpenAPI 0.6.0** (full spec pinned at [`calle-openapi-0.6.0.yaml`](calle-openapi-0.6.0.yaml)),
2026-08-31.

**This supersedes master doc §1.6, §4.6, §5, §5.6 wherever they describe the CALL-E API.**
The master doc's `plan_call → confirm_token → run_call → get_call_run` **do not exist**. Idea,
thesis, verdict model, evidence-span rule, kill-list — unchanged.

---

## 1. Client & auth

- PyPI `calle-ai` v0.7.0 → `import calle`. Clean install on Python 3.14 (deps: `httpx`, `anyio`, `attrs`).
- `from calle import CalleClient`
- `CalleClient(api_key=..., base_url="https://api.heycall-e.com", timeout=30.0, http_client=None)`
- Auth = HTTP `Authorization: Bearer <api_key>` (SDK handles it).
- Namespaces: `client.calls`, `client.goals`, `client.webhooks`. `client.close()` when done.
- Exceptions: `CalleAPIError` (base) · `CalleAuthenticationError` (401) · `CalleRateLimitError`
  (429) · `CalleConnectionError` · `CalleTimeoutError` · `CalleWebhookSignatureError`.

## 2. The 7 endpoints

| Method | Path | SDK call | Notes |
|---|---|---|---|
| POST | `/v1/calls` | `client.calls.create(...)` | one-shot call. `Idempotency-Key` header optional (**we always send one**). 201. |
| GET | `/v1/calls/{id}` | `client.calls.get(call_id)` | full `CallTask`. `call_id` matches `^call_[A-Za-z0-9_-]+$`. |
| GET | `/v1/calls/{id}/events` | `client.calls.list_events(call_id, cursor=, limit=)` | sparse dev events, `limit` ≤ 100 (default 50). |
| GET | `/v1/goals` | `client.goals.list(limit=, after=)` | owner's published goals; `limit` ≤ 100. |
| GET | `/v1/goals/{goal_id}` | `client.goals.get(goal_id)` | `Goal` + `published_run_spec` (input_schema, result_schema, version). |
| POST | `/v1/goals/{goal_id}/runs` | `client.goals.run(goal_id=, phone=, variables=, idempotency_key=)` | `Idempotency-Key` **required**. 201/402/409/422. |
| GET | `/v1/goals/{goal_id}/runs/{goal_run_id}` | `client.goals.get_run(goal_id, goal_run_id)` | poll with `GoalRun.id`, **not** the nested `run_id`. |
| POST | `/calle/webhook` | *(your receiver)* | `client.webhooks.unwrap(...)` / `.verify(...)` (HMAC). |

Convenience: `client.calls.create_and_wait(**kw, interval_seconds=2, timeout_seconds=600)`,
`client.calls.wait_for_result(call_id, ...)`, `client.goals.run_and_wait(...)`,
`client.goals.wait_for_result(goal_id, goal_run_id, ...)`. `wait_for_result` polls until
terminal (`completed|failed|canceled`) or `result`/`error` non-null; raises `CalleTimeoutError`.

## 3. Placing a verification call — Ghostline's primary path (`calls.create`)

```python
from calle import CalleClient
client = CalleClient(api_key=os.environ["CALLE_API_KEY"])

call = client.calls.create(
    task=(
        "You are an automated verification call on behalf of Northline Health. "
        "Disclose at the start that this is an automated call and that no patient "
        "information is being requested. Ask two questions and nothing else: "
        "(1) Do you currently accept Northline Health plan members? "
        "(2) Are you accepting new patients? Keep the call under 90 seconds."
    ),
    recipients=[{"phones": ["+1XXXXXXXXXX"], "region": "US", "locale": "en-US"}],
    result_schema={
        "type": "object",
        "additionalProperties": False,
        "required": ["accepts_plan", "accepting_new_patients"],
        "properties": {
            "accepts_plan": {
                "type": "string", "enum": ["yes", "no", "unknown"],
                "description": "yes only if the responder explicitly confirms Northline Health "
                               "is accepted; no if explicitly denied; unknown otherwise.",
            },
            "accepting_new_patients": {
                "type": "string", "enum": ["yes", "no", "unknown"],
                "description": "yes/no only on an explicit statement; unknown otherwise.",
            },
        },
    },
    metadata={"ghostline_run_id": "gl_...", "record_id": "provider_001",
              "claim_pack": "healthcare", "pack_version": "1"},
    idempotency_key="ghostline:provider_001:healthcare@1",
)
final = client.calls.wait_for_result(call["id"], interval_seconds=4.0, timeout_seconds=600)
```

- **Pass `recipients` explicitly** — never rely on the number being in `task` text. Keeps the
  dial target in trusted structured state (RULES.md §5). `phones[]` pattern `^\+[1-9]\d{6,14}$`.
- `result_schema` supported subset: `type`, `properties`, `required`, `enum`, nested `object`,
  simple `array.items`, `description`, `additionalProperties:false`. **Unsupported:** `$ref`,
  `oneOf`, `anyOf`, `allOf`, recursion, `additionalProperties:true`. → our claim-pack schema
  generator must emit flat enum schemas only.
- CALL-E's own guidance: *"Prefer string enums over booleans… include an `unknown` value when
  the call may not provide enough evidence."* — i.e. CALL-E already does abstention at its layer.
  **Ghostline's added value:** a *verbatim* span (CALL-E's `evidence` is paraphrase), the
  MATCH/MISMATCH-vs-claim comparison, provenance, expiry, corrections, lifecycle.
- `idempotency_key`: byte-stable per (record, pack, version). Reuse with changed params → `409
  idempotency_conflict`. Never randomize per retry.

## 4. The result object — `CallTask` (all listed fields always present)

```
id, object="call_task",
status: queued | in_progress | completed | failed | canceled,
task,
recipients: [ CallTaskRecipient ],
structured_result: object | null,      # task-level, per result_schema; null if unextractable
summary: string | null,
task_completed: boolean | null,        # null until terminal post-summary
completion_confidence: {score:0..1, label} | null,
evidence: [string],                    # PARAPHRASED summary strings, may be []
metadata: object,                      # echoed from create
failure_code: string | null,           # only when status=failed; FREE-FORM string (not enum'd)
failure_message: string | null,
created_at, completed_at: string | null
```

`CallTaskRecipient`: `id, phones, locale, region, status(pending|in_progress|completed|failed|skipped),
structured_result(obj|null, per recipient_result_schema), summary, attempts[]`

`CallTaskAttempt`: `id, phone, status(queued|dialing|in_progress|completed|failed|canceled),
started_at, completed_at, summary, transcript_turns[], provider_call_id, failure_code, failure_message`

`CallTranscriptTurn`: `offset_seconds(int|null,≥0), speaker(bot|user|unknown), text`

> **⚠️ The transcript is at `call["recipients"][i]["attempts"][j]["transcript_turns"]`, not
> top-level.** Multiple attempts = retries; use the attempt with `status == "completed"` (or the
> last one). Extract Ghostline's verbatim span from the concatenated `user` turns of that attempt.

## 4a. MCP path — `plan_call` / `run_call` / `get_call_run` ARE real (they're MCP tools)

The master doc's `plan_call → confirm_token → run_call → get_call_run` was **not wrong** — it
describes the **CALL-E MCP server**, not the SDK. Both exist; they are different integration
surfaces.

- MCP endpoint (Streamable HTTP): `https://seleven-mcp-sg.airudder.com/mcp/openagent_oauth`
- Auth: **OAuth client flow** (not a bearer API key). Never log/expose tokens.
- Tools:
  - `plan_call` — creates/refines a call plan **without dialing**; returns `plan_id` + `confirm_token`.
  - `run_call` — executes a planned call; **requires `plan_id` + `confirm_token` (preserved exactly)**. Places a real call.
  - `get_call_run` — read-only; polls for **activity, transcript, and results**.
- No cancel tool. Parameter/return schemas are not published in text docs — introspect via
  `npx -y @call-e/cli mcp tools` once CLI-authed (Day 1).

**Why this matters:** the `plan_call`/`run_call` split is a genuine two-step "don't dial until
confirmed" primitive. It is the natural fit for the **PR Skill** (`skills/phone-claim-verifier/`),
which runs inside agent environments (Claude Code, Codex, Cursor) where MCP is the integration.
→ Ghostline uses **both surfaces** (D-012):
| Surface | Where | Why |
|---|---|---|
| **Python SDK** (`calle-ai`, `calls.create`) | hosted console + CLI engine | server-side, clean "imported & called at runtime", native batch / idempotency / `result_schema` |
| **MCP** (`plan_call`/`run_call`/`get_call_run`) | the `skills/phone-claim-verifier/` Skill contribution | reusable in agent environments; confirm-token safety pattern; exercises a second CALL-E surface (Technical Implementation depth) |

The hosted app replicates the plan/confirm split as **Ghostline's own Policy Gate** (`plan()`
builds + returns the call spec for approval; `execute()` calls `calls.create`).

## 5. Goal path (`client.goals`) — secondary, "reusable CALL-E-native artifact"

- Goals are **authored & published in the CALL-E Chat dashboard** — not creatable via API.
- `client.goals.run(goal_id, phone, variables, idempotency_key)` → `GoalRun`:
  `object, id, goal_id, run_id (internal — don't poll with it), run_spec{id,version}, status
  (queued|in_progress|completed|failed|canceled), result(obj|null), error(GoalRunError|null),
  created_at, completed_at`. `result` XOR `error`; both null = keep polling.
- `phone` pattern is **stricter**: `^\+[1-9]\d{7,14}$`. `variables` = **flat scalars only**
  (string/number/boolean — no nested objects, arrays, or null), validated against the goal's
  published `input_schema`.
- `GoalRunError.code`: `call_failed | no_answer | declined | timed_out | canceled |
  result_invalid | result_unavailable | result_failed` + `detail_code` (e.g. `no_human_answered`).
- **Decision D-008:** build on `calls.create` (claim pack = in-repo, reproducible config).
  Optionally publish ONE goal and demo `goals.run` as a bonus.

## 6. Error taxonomy → Ghostline verdicts

**`APIError.code`** (on `POST /v1/calls` etc.; HTTP 400/401/403/409/422/429/500):
`invalid_request, unauthorized, forbidden, rate_limit_exceeded, insufficient_balance,
unsupported_region, unsupported_language, recipient_blocked, policy_violation, call_not_ready,
no_recipients, invalid_recipient, invalid_phone, result_schema_invalid,
recipient_result_schema_invalid, idempotency_conflict, goal_not_published, goal_not_executable,
goal_not_ready, schema_override_not_allowed, variables_invalid, provider_unavailable,
internal_error, not_found`

| Signal | Ghostline verdict | Diagnostic tag | Action |
|---|---|---|---|
| `status=completed` + verbatim span found | MATCH / MISMATCH | — | write attestation |
| `status=completed`, no verbatim span | **UNCLEAR** | `AMBIGUOUS`/`LOW_CONFIDENCE` | abstain (the thesis) |
| `status=failed`, `failure_code` ~ no-answer/voicemail/IVR | NO_CONTACT | `NO_ANSWER`/`VOICEMAIL`/`IVR` | **capture real strings Day 1 — not enumerated in spec** |
| `status=failed`, other | NO_CONTACT | `CALL_FAILED` | log `failure_message` |
| `APIError: invalid_phone`/`invalid_recipient`/`no_recipients` (pre-dial) | NO_CONTACT | `INVALID_NUMBER` | never counts against call budget |
| `APIError: unsupported_region`/`unsupported_language` | NO_CONTACT | `UNSUPPORTED_REGION` | **the international-routing risk, with a clean signal** |
| `APIError: insufficient_balance` | — (no verdict) | — | trip credit-floor → Replay fallback |
| `APIError: rate_limit_exceeded` (`CalleRateLimitError`) | — (retry) | — | backoff + retry |
| `recipient_blocked`/`policy_violation` | NO_CONTACT | `BLOCKED` | surface to user, do not retry |

## 7. Genuine gaps found (→ [FEEDBACK.md](FEEDBACK.md) — Most Valuable Feedback material)

1. **No cancel endpoint.** `status` has `canceled` but there is no `POST /v1/calls/{id}/cancel`
   / DELETE. An in-flight call cannot be stopped via API — "cancellation" is client-side only
   (stop polling; the call still completes and bills). → master doc §5.6/§5.10 "cancel an
   in-flight job" is **not implementable**; amend to "abandon polling; document that the call
   still completes."
2. **No push/SSE transcript stream.** There is no websocket or server-sent-events surface;
   `/v1/calls/{id}/events` returns coarse lifecycle events (`call.completed`), not per-turn
   text. **However** — MCP `get_call_run` is documented to poll "activity, **transcript**, and
   results", and nothing in the OpenAPI says `transcript_turns` are withheld until terminal
   (`in_progress` is a valid status to `GET` against). So a **near-live feed by polling
   `client.calls.get(call_id)` every ~3-5 s during `in_progress`** is plausibly available with a
   few seconds' lag. **Confirm with the first real call (Day 1).** If partial turns don't
   appear until terminal: fall back to a status progress indicator (queued→in_progress→
   completed) + full transcript reveal on completion, and soften the demo §10.2 "streams live"
   beat to "the call completes, then the transcript and verdict resolve on screen."
3. **One-shot `failure_code` is an un-enumerated free string** (only the Goal path has the clean
   `GoalRunError` enum). Inconsistent; forces us to reverse-engineer failure strings from live
   calls. Feedback: expose the same enum on `CallTaskAttempt.failure_code`.
4. **No audio/recording URL** anywhere in the API. Reasonable for privacy, but kills master doc
   cherry (e) as written → replace with confidence-colored transcript replay (D-010, below).
5. Webhook signature header names (`timestamp`, `signature`) aren't in the OpenAPI — only in SDK
   source. Minor doc gap.

## 8. Confirmed good for Ghostline

- `result_schema` / `recipient_result_schema` = native structured output → direct claim mapping
  + a second extraction to cross-check ours against.
- `recipients[]` = native batch.
- `Idempotency-Key` = native dedup (the "no duplicate calls" safety rule is a header).
- `metadata` echoed on call **and** webhook → audit-trail correlation for free.
- `region`/`locale` per recipient → real inputs for the timezone cherry (k).
- `webhooks.verify`/`unwrap` (HMAC) → the hosted console can use `webhook_url` + a receiver
  instead of long-poll (use for console; CLI slice stays on polling for simplicity).
- `completion_confidence` + `task_completed` → store in provenance as CALL-E's own read, for
  the "Ghostline abstained where CALL-E was confident" demo beat.

## 9. Day-1 live-account checklist (entrant)

- [ ] `client.calls.create_and_wait(task="call <my own line>, ask if they can hear you",
      result_schema={...yes/no/unknown...})` → **save the full result JSON verbatim** as replay
      fixture #1 (this is our ground-truth shape).
- [ ] Repeat to an **international / Singapore** number → confirm no `unsupported_region`.
- [ ] Call a number that rings out / goes to voicemail → **record the exact `status` +
      `failure_code` + `failure_message` strings**. Repeat for a busy signal if possible.
- [ ] Inspect `client.calls.list_events(call_id)` output — what event `type`s actually appear.
- [ ] Dashboard → Billing: confirm free-call balance. Dashboard → Goals: is there a starter goal?
- [ ] Note anything confusing → `FEEDBACK.md`.
