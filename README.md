# Ghostline

**A phone-powered data-verification engine.** Give it a table of records and a claim pack;
it calls the numbers via CALL-E, extracts what the human actually said **with a mandatory
verbatim evidence span**, and returns **MATCH / MISMATCH / UNCLEAR / NO CONTACT** — never a
guess it can't support — plus a `corrections.csv` someone can act on.

> Ghostline doesn't claim truth. It creates a timestamped, evidence-backed record of what a
> specific human source said — and tells you when reality has moved on.

Built for the **CALL-E: Your Code Is Calling** hackathon.

The lifecycle: **asserted → verified → evidenced → corrected → expired → re-verified.**

---

## Why a phone call

The facts that rot fastest in an operational database — "is this office still here", "do they
still accept this plan", "is this still the right contact" — don't live in any API. They live
in a person's head and decay constantly. No scrape, no portal, no chatbot can retrieve them.
Only a phone call can. CMS found **48.74%** of Medicare Advantage provider-directory locations
had at least one inaccuracy; the fix has to talk to a human.

## The one rule that makes it trustworthy

**Evidence-span-or-abstain.** A `MATCH` or `MISMATCH` verdict is *impossible* to produce
unless the extractor identifies a verbatim quoted span from a responder's turn that supports
it. No span → forced `UNCLEAR`. This is a hard check in [`ghostline/verdict.py`](ghostline/verdict.py),
not a README promise:

```
Claim: "currently accepts Northline Health"
Responder: "We take most major commercial plans here."
Verdict: UNCLEAR — no span names the plan. (CALL-E's own extractor guessed "yes", high confidence.)
```

## Quick start

```bash
pip install -e ".[dev]"
cp .env.example .env          # add CALLE_API_KEY (and LLM_API_KEY for the real extractor)

ghostline packs               # list claim packs
ghostline replay              # run the full pipeline over 9 fixture calls — 0 live calls
ghostline verify examples/providers-sample.csv --pack healthcare          # dry run: shows planned calls
ghostline verify examples/providers-sample.csv --pack healthcare --live   # places real CALL-E calls

uvicorn ghostline.console.app:app --port 8000      # the web console
```

`replay` and dry-run `verify` never touch CALL-E. Only `--live` spends a call.

### Web console

One screen: type a record (or upload a CSV), pick a claim pack, choose **Replay** (explore 9
recorded scenarios, no calls) or **Live** (Ghostline calls the number you entered). The result
page streams to a verdict with the evidence span highlighted in the transcript, and a
`corrections.csv` download. `GET /health` reports mode + config for uptime checks.

## How CALL-E powers it

| Step | CALL-E |
|---|---|
| Build the call | `PolicyGate.plan()` turns a claim pack + record into a `task` string + a JSON-Schema `result_schema` |
| Place it | `client.calls.create(task, recipients=[{phones,region,locale}], result_schema, idempotency_key)` |
| Wait | `client.calls.wait_for_result(call_id)` — poll to a terminal state |
| Read | normalize `recipients[].attempts[].transcript_turns[]` → our `Transcript` |
| Verify | our own extractor pulls a **verbatim** span; CALL-E's `structured_result` / `completion_confidence` are kept only as a secondary signal |

The reusable contribution is [`skills/phone-claim-verifier/`](skills/phone-claim-verifier/) —
a portable Agent Skill (stdlib-only scripts + `SKILL.md`) for the CALL-E **MCP** surface
(`plan_call` → `run_call` → `get_call_run`). `plan.py` turns records + a claim pack into call
goals; `verdict.py` enforces evidence-span-or-abstain on the agent's extraction and writes the
corrections file. See [`Docs/research/CALL_E_INTEGRATION.md`](Docs/research/CALL_E_INTEGRATION.md).

## Extending to a new domain

Write a claim pack — a YAML file. Bundled packs live in [`ghostline/data/packs/`](ghostline/data/packs/);
drop your own into a `packs/` or `examples/` dir at the repo root and it's picked up. That's the
whole change — the engine is domain-neutral. Healthcare is the flagship *evidence* case, not the
product's identity.

```yaml
pack_id: suppliers
display_name: Supplier contact records
expires_after_days: 180
claims:
  - claim_id: still_supplies_us
    question: Do you still supply parts to Harbor Manufacturing under contract HM-2231?
    expected_type: boolean
    subject_terms: ["harbor manufacturing", "hm-2231", "the contract"]
```

## Architecture

```
CSV / manual form ─┐
                   ├─► Record ─► PolicyGate.plan ─► CallPlan ─► CallEngine ─► CALL-E
Replay fixtures ───┘                  (allowlist, E.164,          │
                                       credit floor, hours)       ▼
                                                            Transcript (normalized)
                                                                  │
                                                       Extractor (verbatim span required)
                                                                  │
                                                    verdict.evaluate  ◄── evidence-span-or-abstain
                                                                  │
                                                 Attestation ─► corrections.csv
```

Module map: [`ghostline/models.py`](ghostline/models.py) ·
[`claim_pack.py`](ghostline/claim_pack.py) · [`policy_gate.py`](ghostline/policy_gate.py) ·
[`call_engine.py`](ghostline/call_engine.py) · [`calle_normalize.py`](ghostline/calle_normalize.py) ·
[`extractor.py`](ghostline/extractor.py) · [`verdict.py`](ghostline/verdict.py) ·
[`corrections.py`](ghostline/corrections.py) · [`replay.py`](ghostline/replay.py) ·
[`cli.py`](ghostline/cli.py)

## Tests

```bash
pytest -q          # 31 tests: evidence-span enforcement, dial allowlist, prompt-injection
                   # resistance, expiry, corrections filtering, claim-pack loading, 9 fixtures
ruff check ghostline tests
```

## Safety

- A dial target comes **only** from `Record.phone` (a parsed CSV row or a validated form
  field). No number from a transcript, an LLM output, or any model text can reach the dialer.
  Tested in [`tests/test_policy_gate.py`](tests/test_policy_gate.py).
- Dry-run by default. Session live-call cap + a hard credit floor that falls back to Replay Mode.
- Every call opens with a disclosed automated-call identity and requests no personal information.
- All names in this repo are fictional (`Northline Health`, `Harbor Point Medical`, …).

## Limitations

- CALL-E has no call-cancellation endpoint — an in-flight call can't be stopped, only
  un-watched (it still completes and bills).
- CALL-E exposes no call audio; the review UI replays the transcript, not a recording.
- One-shot-call failure codes aren't enumerated by the API; the voicemail/IVR mapping in
  `calle_normalize.py` is refined from real calls.

See [`Docs/`](Docs/) for the full project documentation.
