# CALL-E — Feedback Log (for the Most Valuable Feedback prize)

Running log of real friction, gaps, and suggestions found while building Ghostline. Submit via
the official CALL-E Feedback Survey during the Feedback Period (through **Sep 18, 2026** — after
the Sep 14 build deadline). One submission per entrant; scored on completeness, viability,
potential impact. **Do not manufacture criticism** — only log what actually cost time or risk.

Format: `[YYYY-MM-DD] AREA — observation → suggested fix (impact)`

---

## API design

- **[2026-08-31] Calls API — no cancel endpoint.** `CallStatus` includes `canceled` and
  `AttemptStatus` includes `canceled`, but there is no `POST /v1/calls/{id}/cancel` or `DELETE
  /v1/calls/{id}` in OpenAPI 0.6.0. An in-flight call cannot be stopped programmatically; the
  caller can only stop polling while the call (and its charge) proceeds. → Add a cancel
  endpoint, or document explicitly that calls are uncancellable and why. (Impact: high — matters
  for cost control, runaway-job safety, and any UI with a "stop" button.)

- **[2026-08-31] Calls API — `failure_code` is an un-enumerated free-form string**, while the
  Goal path has a clean `GoalRunError.code` enum (`no_answer`, `declined`, `timed_out`, …). The
  asymmetry forces one-shot-call integrators to reverse-engineer failure strings from live
  calls to build reliable branching. → Expose the same (or a superset) enum on
  `CallTaskAttempt.failure_code` / `CallTask.failure_code`. (Impact: high — failure handling is
  most of the real work in a phone agent.)

- **[2026-08-31] Calls API — no live/interim transcript.** `transcript_turns` only appear on
  the terminal `CallTask`; `/v1/calls/{id}/events` emits coarse lifecycle events
  (`call.completed`) with no partial transcript. Building a "watch the call happen" UX (a very
  natural thing to want, and shown in CALL-E's own marketing) isn't possible from the API. →
  Stream interim transcript turns via events or a websocket. (Impact: high for product/demo UX.)

- **[2026-08-31] Docs — the SDK method names don't match community/reference material.** Older
  material referenced `plan_call` / `run_call` / `get_call_run`; the shipped SDK v0.7.0 is
  `client.calls.create` / `.get` / `.wait_for_result` and `client.goals.run`. A short
  "canonical API surface" table near the top of the quickstart would save integrators a
  reconciliation pass. (Impact: medium.)

## SDK (`calle-ai` v0.7.0)

- **[2026-08-31] Package/module name mismatch.** PyPI package is `calle-ai`; import module is
  `calle`. Common footgun (`import calle_ai` → `ModuleNotFoundError`). → Note it prominently in
  the install guide, or ship a `calle_ai` shim that re-exports. (Impact: low, high-frequency.)

- **[2026-08-31] Webhook verification header names absent from OpenAPI.** `client.webhooks.verify`
  takes `timestamp` and `signature` but the OpenAPI spec doesn't document which request headers
  carry them (only `CALL-E-Event-Id` is specified). → Document the signature header names in the
  webhook section. (Impact: medium — blocks secure webhook adoption.)

- **[2026-08-31] Building the webhook path, the signature-header gap actually bit.**
  `client.webhooks.unwrap(raw_body, headers, secret)` is the right call for a serverless
  receiver, but with no documented header names there's no way to write a conformance test or
  reason about failure modes without a live webhook to inspect. A two-line "we send
  `CALL-E-Signature` and `CALL-E-Timestamp`" (or whatever they are) in the webhook docs would
  unblock this entirely. (Impact: medium-high for anyone on Vercel/Cloudflare/Lambda.)

- **[2026-08-31] Result shape differs between `calls` and `goals`.** One-shot calls return
  `structured_result` + `evidence` (array) + `completion_confidence`; goal runs return
  `result` XOR `error` with a clean `GoalRunError` enum. An integrator who prototypes with
  `calls` and later moves reusable workflows to `goals` has to rewrite their result handling.
  A shared "terminal outcome" envelope, or at least a mapping table in the docs, would help.
  (Impact: medium.)

- **[2026-08-31] `result_schema` silently drops unsupported constructs.** The docs list what's
  supported (`type/properties/required/enum/...`) and what isn't (`$ref/oneOf/anyOf/...`), but
  it's unclear whether an unsupported construct is rejected at `create` time or silently
  ignored during extraction. A `result_schema_invalid` error on `create` for anything
  unsupported (rather than at extraction) would fail fast. (Impact: low-medium.)

## Onboarding

- **[2026-08-31] No obvious "Sign up" entry point.** heycall-e.com's CTA is "START CALLING" →
  `dashboard.heycall-e.com/login`; there's no "Sign up" label, and the install guide / quickstart
  don't link the signup step. A new user looking for account creation has to guess. → Add an
  explicit "Create account" link + a first step in the quickstart. (Impact: medium.)

## (add live-testing findings here from Day 1+)
