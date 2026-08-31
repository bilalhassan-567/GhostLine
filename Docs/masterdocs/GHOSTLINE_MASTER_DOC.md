# GHOSTLINE — Master Project Document
### Birth-to-Grave Build Bible for the CALL-E Hackathon
**Project:** Ghostline — a phone-powered data-verification engine
**Hackathon:** CALL-E: Your Code Is Calling
**Sponsor/Administrator:** AIRUDDER Pte Ltd (Singapore)
**Document owner:** you (single-entrant / Representative)
**Document version:** 1.0 — final, pre-build
**Timezone used throughout this doc:** GMT+5 (matches both the hackathon's official schedule and Lahore/PKT — no conversion needed)

> **How to use this document:** this is the single source of truth for the entire run of the project, from today until prize delivery. Every decision, date, rule citation, and cut-line lives here. If something in a chat, a Discord message, or a Devpost update contradicts this doc, update this doc first, then act. Keep this file in the repo root as `docs/MASTER.md` and update it as you go — treat it as living, not archival.

---

## 0.5 AMENDMENTS LOG — read before implementing anything

*Added 2026-08-31 after CALL-E account creation, SDK/OpenAPI verification, and a re-check of the
live hackathon page. The body of this doc below is otherwise unchanged; where it conflicts with
an entry here, **this log wins**. Rationale and detail live in `Docs/research/` and
`Docs/planning/DECISIONS.md`.*

**A1 — Timeline re-anchored.** This doc was written Aug 18 (27 days out). Real start: Aug 31.
Compressed day-by-day plan: `Docs/planning/ROADMAP.md` (supersedes §8's dated table; §8's
sequencing principle and cut-order still hold). Submit target **Sep 12**; deadline **Sep 14,
8:45 PM GMT+5 = 11:45 PM SGT** — these are the *same instant*; §1.1's note that "11:45 PM SGT"
is wrong is itself mistaken (the local GMT+5 time it gives is right). Judging window opens
7:00 AM GMT+5 Sep 30, not 6:00.

**A2 — CALL-E API surface (supersedes §1.6, §4.6, §5.2, §5.6).** `plan_call → confirm_token →
run_call → get_call_run` are **MCP tool names**, not the SDK. Verified surfaces:
- **Python SDK** `calle-ai` v0.7.0 (`import calle`): `client.calls.create(task=, recipients=,
  result_schema=, metadata=, idempotency_key=)` → `client.calls.wait_for_result(call_id)` /
  `.get(call_id)` / `.list_events(call_id)`; `client.goals.run(goal_id, phone, variables,
  idempotency_key)`; `client.webhooks.verify/unwrap`. Auth = bearer API key. **No plan/confirm
  step — `create` dials immediately.**
- **MCP** (OAuth, `https://seleven-mcp-sg.airudder.com/mcp/openagent_oauth`): `plan_call`
  (returns `plan_id`+`confirm_token`, no dial), `run_call` (needs both), `get_call_run`.
- **Decision (D-012):** SDK powers the hosted console + CLI engine; MCP powers the
  `skills/phone-claim-verifier/` Skill PR. Both surfaces used deliberately.
- Full reference: `Docs/research/CALL_E_INTEGRATION.md` + pinned `calle-openapi-0.6.0.yaml`.

**A3 — Policy Gate is fully client-side (supersedes §4.6 flow).** No `plan_call`/`confirm_token`
in the SDK path. Ghostline's own Policy Gate (allowlist, E.164, business hours, cadence cap,
credit floor) is the *only* thing between trusted state and `calls.create`. It also exposes a
two-step `plan()` / `execute()` split so the UI can show the exact call for human approval
before dialing (this is how derived calls §4.10 and manual entry §4.7 get their approval gate).

**A4 — Ghostline runs its own extraction (refines §4.4, §5.5).** CALL-E returns its *own*
`structured_result` + `evidence` (paraphrased summary strings) + `completion_confidence`.
Ghostline still runs its own pass over `recipients[].attempts[].transcript_turns[]` and enforces
a **verbatim** span. CALL-E's outputs are stored as a *secondary* signal in provenance. New
demo beat: Ghostline returns UNCLEAR where CALL-E's `completion_confidence` was "high".

**A5 — `result_schema` constraints.** Supported: `type, properties, required, enum, nested
object, simple array.items, description, additionalProperties:false`. **Not** supported: `$ref,
oneOf, anyOf, allOf, recursion, additionalProperties:true`. Claim-pack → schema generator must
emit flat enum schemas. CALL-E recommends `enum:[yes,no,unknown]` with `unknown` for weak
evidence — use exactly that.

**A6 — No call cancellation exists (supersedes §5.6, §5.10).** No cancel endpoint / MCP tool.
"Cancellation" = Ghostline stops polling and marks the verification abandoned; the CALL-E call
still completes and bills. Document as a known limitation (the submission repo asks for
"cancellation notes" — this *is* the note).

**A7 — No push/SSE transcript stream (affects §5.2, §10.2).** Near-live feed *may* be available
by polling `calls.get()` during `in_progress` — **confirm on the first real call (Day 1)**. If
not: status progress indicator + full transcript reveal on completion; soften the video's
"transcript streams live" line accordingly.

**A8 — No audio/recording API (supersedes §3 kill-list note, §4.12e).** CALL-E exposes no
recording URL. Cherry (e) "audio playback" → **"confidence-colored transcript replay"**
(re-render `transcript_turns` with timing, highlight the span, color by confidence). Same review
value, no audio. The kill-list rule about not publishing third-party voices is now moot for the
API path but stays as guidance.

**A9 — Full scope confirmed (entrant, 2026-08-31).** Build everything in this doc — all 13
cherries (with A8's swap), both packs demoed, derived calls, 40–50-call benchmark. §8.1 cut
order is a slip-triggered contingency only.

**A10 — Additional-calls form prerequisites (refines §1.7).** Must (1) be Devpost-registered
for the hackathon and (2) have logged into CALL-E once, *before* submitting the form.
First-come-first-served while supplies last; form's own cutoff Sep 14 12:00 PM SGT. Submitted
2026-08-31.

**A11 — CLI is not a binding integration path (refines §1.4).** The binding Project Requirements
clause names "API or SDKs for Python/TypeScript, or CALL-E Skill or MCP" — CLI is marketing
copy only. Our runtime path is the SDK (+ MCP for the Skill).

---

## 0. TL;DR — the one-paragraph version

Ghostline is a phone-powered data-verification engine: give it a table of records and a set of claims, it calls the relevant phone numbers via CALL-E, asks the questions, extracts what the human actually said with mandatory evidence, and returns **MATCH / MISMATCH / UNCLEAR / NO CONTACT** — never a guess it can't support — plus a corrections file someone can act on immediately. There is one flow, not a special demo mode: records get added either by **CSV upload** (batch) or by **typing one in directly** on the same form (§4.7) — so anyone, including a judge, tries the real product by typing their own name and phone number into the same box every other user uses, and Ghostline calls them, live. Replay Mode (zero live calls, fixture-based) exists separately for safe, unlimited exploration. The flagship evidence domain is U.S. health-plan provider directories (CMS/AJMC/Senate Finance data below), generalized via a domain-neutral "claim pack" architecture to supplier/CRM records and community-service directories, proving reusability rather than asserting it — and a user can describe *any* domain in plain English to have a claim pack auto-generated for human approval (§4.12a), making "works for any domain" a demonstrated capability, not just an assertion. On top of the core loop sit thirteen cheap, high-delight additions (§4.12) — auto-suggested recheck intervals, one-click escalation to a better source, plain-English batch summaries, private per-call audio playback, a duplicate-number guard, confidence-colored transcripts, a re-verification diff view, a live call-budget meter, timezone-aware scheduling, a "try it yourself" QR code, and a per-number trust score — each independently cuttable and none load-bearing. The whole product statement is a lifecycle:

> **asserted → verified → evidenced → corrected → expired → re-verified**

---

## 1. HACKATHON FACTS — verified against the Official Rules and the live schedule you provided

### 1.1 Dates (all times **GMT+5**, which is Lahore/Pakistan local time — no conversion needed)

| Period | Begins | Ends |
|---|---|---|
| **Submissions** | Jul 23, 2026, 6:30 PM | **Sep 14, 2026, 8:45 PM** |
| Feedback | Jul 23, 2026 | Sep 18, 2026, 11:45 PM SGT (≈ Sep 18, 10:45 PM GMT+5) |
| Judging | Sep 30, 2026, 6:00 AM | Oct 13, 2026, 2:00 PM |
| Winners announced | — | ~Oct 19, 2026, 11:00 AM |

⚠️ **Correction from earlier drafts of this project's planning:** the submission deadline is **8:45 PM GMT+5 on Sep 14**, not 11:45 AM/PM SGT as earlier overview pages suggested. Since GMT+5 = Pakistan Standard Time, **this is simply 8:45 PM your local time on Sep 14 — no timezone math required.** Per Official Rules §11, if any hackathon material conflicts with the Official Rules, the Official Rules control — but this schedule (from the live hackathon page) is the most current and authoritative source and is the one this doc plans against. Re-check the schedule page once more in the final week in case of amendment (Rules §11: amendments take effect on posting).

**Days remaining from today (Aug 18, 2026) to submission: 27 days.** Build plan below uses 27, not 26 — recheck against today's actual date when you start executing.

### 1.2 Sponsor / eligibility / conflict-of-interest facts that affect this project specifically

- Sponsor: **AIRUDDER Pte Ltd**, Singapore. AI Rudder is an enterprise voice-AI company — keep this in mind for framing (see §7.2).
- You must be at or above age of majority in your country of residence. Pakistan is not on the exclusion list (US-sanctioned/prohibited list: Brazil, Quebec, Russia, Crimea, Cuba, Iran, North Korea, OFAC-sanctioned territories).
- **Do not** let anyone employed by AIRUDDER, a CALL-E judge, or their immediate family/household contribute to the build — automatic disqualification risk.
- **A project can only win ONE prize.** Do not try to straddle "Most Practical" and "Most Innovative" in the copy — pick a lane (this doc recommends **Most Practical**, $4,000, with Innovative as credible upside — see §7.1).
- **Feedback Prize is separate, per-individual, and stacks with a project prize** — but if you *only* submit feedback (no project), you're excluded from the main prizes. Do both.
- Multiple submissions allowed if "substantially different." Not recommended here — focus all 27 days on one submission.

### 1.3 What counts as a valid submission (per Devpost forum clarification, Derek @ CALL-E, and Official Rules)

> *"We welcome PRs in any form—including standalone skills, plugins, or functional apps. Just make sure your submission includes a clear, sufficient demo showing how it works with CALL-E."* — Derek @ CALL-E, official forum answer

This confirms: **Ghostline can ship as a functional app (the console) AND a skill/plugin PR simultaneously** — which is exactly the plan (§4). You are not forced to pick one lane; the two-repo structure (see §1.5) expects most serious entrants to have both a working app and a PR.

### 1.4 Judging mechanics — read this twice, it changes strategy

- **Stage One (pass/fail):** does it reasonably fit the theme and reasonably use CALL-E (API/SDK/MCP/CLI/Skill)? Binary gate. Ghostline passes trivially if `plan_call`/`run_call`/`get_call_run` are genuinely wired in.
- **Stage Two — four criteria, EQUALLY WEIGHTED (25% each):**
  1. **Real World Impact** — real, specific phone-work problem; credible for real users; worth building further; NOT a generic "AI that calls people" concept.
  2. **Quality of the Idea** — creative, non-obvious CALL-E use, genuine problem-space understanding; contribution "clear, well-scoped, and reusable by the community."
  3. **Technical Implementation** — thoroughness/skill of CALL-E usage; genuine effort; **CALL-E imported and actually called at runtime, not just referenced.**
  4. **Product Experience & Demo** — complete, coherent experience; demo video clearly communicates what and why.
- **Tie-break order:** ties resolve on criterion #1 first (Real World Impact), then #2, then #3, then #4, then judge vote. **Strategic implication:** Ghostline's strongest axis (Impact) is also the first tiebreaker — reaching a tie at the top is a winning position, not a consolation.
- **Judges may test your live app** — "Access must be provided... available free of charge and without any restriction, for testing, evaluation and use by the Sponsor, Administrator and Judges until the Judging Period ends" (i.e., through **Oct 13**, a full month after you submit). **Judges are not required to test it** and may judge on video/description alone — so the video must stand completely on its own, AND the live app must survive unattended for a month if they do check.
- Judges "may be employees of the sponsor," may change, may judge in rounds — treat every judge as an AI Rudder domain expert who will notice a shallow CALL-E integration immediately.

### 1.5 The two-repository rule — do not confuse these

| Repo | Purpose | What you do with it |
|---|---|---|
| [`CALLE-AI/call-e-integrations`](https://github.com/CALLE-AI/call-e-integrations) | **Setup.** Install guide, MCP/SDK/API/CLI/Skill quickstarts, runnable examples, CLI reference. | You *read* this. Install the `calle` skill/CLI from here. Never open a submission PR here. |
| [`CALLE-AI/awesome-phone-call-agents`](https://github.com/CALLE-AI/awesome-phone-call-agents) | **Submission.** Community hub for Agent Skills, Workflow Plugins, User-facing Apps. | You **open your PR here**, in the correct Contribution Area folder (`skills/`, `plugins/`, or `apps/` per the README), following `docs/git-naming-conventions.md`, and passing `python3 scripts/validate_repository.py`. |

**Ghostline goes in `skills/` as `skills/phone-claim-verifier/`**, with the hosted console referenced from the `SKILL.md` and also listed under `apps/` if you want an explicit app-directory entry too (recommended: do both — it costs one README stub and covers "functional app" and "reusable skill" simultaneously, satisfying Derek's clarification maximally).

### 1.6 Resources — bookmark, don't re-derive

- Install guide: `https://github.com/CALLE-AI/call-e-integrations` → `docs/install/install-guide.md`, troubleshooting at `docs/install/troubleshooting.md`
- Docs/API reference: `https://docs.heycall-e.com/` (`#/sdks`, `#api-reference`)
- Product overview: heycall-e.com
- Inspiration repo: `https://github.com/CALLE-AI/awesome-phone-call-agents` — reference skills `call-reminder`, `google-form-callback`, `outbound-call-skill-creator`; runnable apps `apps/python/batch-runner`; plugin example `plugins/n8n-calle-api`
- Support: **CALL-E Discord** — `https://discord.gg/6AbXUzUV8w`. Use this the moment you hit friction; also mine it for feedback-prize material.
- CLI reference (canonical): `packages/cli/docs/cli-reference.md` in `call-e-integrations`. Commands you will use directly: `calle auth login`, `calle auth status`, `calle mcp tools`, `calle call plan`, `calle call start`, `calle call run`, `calle call status`. Options you will actually touch: `--to-phone`, `--goal`, `--language`, `--region`, `--timezone`, `--plan-id`, `--confirm-token`, `--run-id`.
- MCP tools your code calls at runtime: **`plan_call` → `run_call` → `get_call_run`**.

### 1.7 Call budget — the hard constraint on everything

- New account: **20 free calls**, automatic.
- Additional: **up to 200 more** via the request form. Processed 1–5 business days, **sole discretion of Sponsor, not guaranteed, "while supplies last."** No auto-billing if exhausted — access just pauses.
- **Action for today:** submit the additional-calls request form the moment you finish reading this doc. Do not wait.
- **Budget allocation (plan against 220 total, revise once approval lands):**

| Purpose | Calls | Notes |
|---|---|---|
| Setup/integration smoke tests (incl. 1 intl. test call) | 10 | Day 1 |
| Core-loop debugging | 30 | Days 4–9 |
| Reliability benchmark (real, human-labelled) | 50 | Day 19 — see §5.9 |
| Demo recording takes | 20 | Day 22 (expect 3–4 attempts/shot) |
| Buffer | 20 | Anywhere |
| **Reserved — untouched — for the Judging Period (Sep 30–Oct 13)** | **80** | For live calls triggered by anyone using the hosted app, rate-limited (§4.8) |
| **Reserve floor — live calls auto-fall-back to Replay-only below this** | 10 | Hard-coded floor, see §5.6 |

Never let development or demo-taking eat into the 90 reserved for judging. Enforce this with a code-level counter, not memory.

---

## 2. THE IDEA — final, locked, one sentence

> **Ghostline takes a table of claims about the offline world, calls the relevant number, records what it was told and who told it, returns MATCH / MISMATCH / UNCLEAR / NO CONTACT with the verbatim evidence, refuses to guess, and produces a corrections file — then lets it happen again when the attestation expires.**

### 2.1 The lifecycle (this is the actual pitch — lead every artifact with it)

```
ASSERTED → VERIFIED → EVIDENCED → CORRECTED → EXPIRED → RE-VERIFIED
   ↑                                                          │
   └──────────────────── (next generation) ─────────────────┘
```

A database record is **asserted** at creation, gets **verified** by a real phone call, the call produces **evidence** (a quoted span, a source role, a timestamp), a discrepancy becomes a **correction**, every attestation **expires** on a domain-appropriate clock, and expiry triggers **re-verification** — closing the loop. Every section of this doc, every screen, every line of the video script, should trace back to one of these six words.

### 2.2 Why this beats the field (recap of the research — see §9 for full citations)

- CMS's own national review found **48.74%** of Medicare Advantage directory locations had at least one inaccuracy; per-plan rates ranged from 4.63% to 93.02%.
- Senate Finance Committee's secret-shopper study (n=120 calls) found only an **18%** appointment-booking success rate and >80% "ghost" listings.
- AJMC (2024) found **40.3%** of *already-known* inaccuracies persisted an average of **540 days** against a 90-day federal standard.
- The **REAL Health Providers Act** (§6220, Consolidated Appropriations Act 2026, signed Feb 3, 2026) makes *measuring* directory accuracy a federal statutory obligation for the first time — compliance effective plan year 2028, public CMS-published scores from plan year 2029. State this narrowly: implementation details are still being finalized (CMS/ONC comment period ran through June 2026).
- CAQH: provider directory maintenance costs U.S. practices **$2.76B/year**, ~$999/practice/month, ~1 staff-day/week.
- Health Affairs/Yale: patients hitting a directory error were **2×** more likely to be treated out-of-network and **4×** more likely to get a surprise bill.

**The insight that makes this a product, not a healthcare compliance tool:** the fact "is this office still here, does it accept this plan, is this person still the contact" doesn't live in any API. It lives in a human's head and decays constantly. No web scrape, no attestation portal, no chatbot can retrieve it. Only a phone call can. That generalizes far beyond healthcare (supplier/CRM contacts, community-service hours, any B2B record with a phone number attached) — which is why the core engine is domain-neutral and healthcare is the flagship *evidence case*, not the product's identity.

---

## 3. WHAT WE ARE **NOT** BUILDING — the kill list (read before touching code)

These were all considered and explicitly cut across three rounds of adversarial review. Do not resurrect them under schedule pressure — they are precisely the kind of "impressive" scope that eats the days you need for the core flow and the PR.

| Cut | Why |
|---|---|
| "Advertised 1,240 → Effective 214" style scale claims | Requires literally 1,240 real calls to be honest. Fabricating it is the single mistake that would sink a project whose entire thesis is evidentiary honesty. |
| Wilson confidence intervals / statistical sampling frames | Real statistics, wrong project stage. Belongs post-hackathon once you have thousands of real calls. |
| Public "Ghost Index" registry | Great v2-of-the-startup idea. Zero hackathon-day value. |
| FHIR ingestion | Nobody is judging FHIR compliance. CSV is sufficient and faster to build. |
| Network-adequacy recomputation / duplicate-cluster detection | Interesting, unnecessary, expensive in dev time. |
| Six-state verdict taxonomy in the primary UI | Confusing. Collapse to 4 visible states (§5.4); keep richer internal diagnostics. |
| Real receptionist voices played **publicly** (in the video, on a public results page) without signed release | Rules §7 (privacy/publicity rights) + §Submission Requirements (no unlicensed material). **Note:** *private* in-app audio playback for the person who ran the verification is a supported feature (§4.12) — the line being cut here is *public broadcast* of someone else's voice, not audio playback as a feature. |
| Real clinic/insurer/brand names or logos on screen | Rules: "must not include third party trademarks." Use fictional names (`Northline Health`, `Northline Family Clinic`, `Harbor Supply Co.`, `Community Bridge Services`). |
| Recruiting an external consented human panel of real clinics | High schedule risk (recruitment, time zones, scheduling), and the manual-entry path (§4.7) makes it redundant — you become the receptionist for demo purposes, then anyone trying the app, including a judge, does the same for themselves. |
| 3 fully-demoed claim packs | 2 demoed (healthcare + supplier/CRM) + 1 written as a 10-line config example (community services) proves generality more efficiently. |
| A giant analytics dashboard | The primary UI is a workflow, not a BI tool. One screen: record → call → evidence → verdict → correction. |
| Confusion-matrix-as-demo-centerpiece | One line on screen ("41 calls · X% agreement · Y% abstained"), full matrix in the README. |

**Tiering rule for everything in this doc, including new features added after this doc's first draft:** every feature is either **Core** (the engine breaks its promise without it — never cut), **Cherry** (cheap, reuses data/machinery the Core already produces, adds delight or polish — build only after Core works end-to-end), or **Post-hackathon** (real idea, wrong week — write it down, don't build it). §4.12 below is entirely Cherry tier. If a Cherry feature is taking more than ~1 day, it has quietly become a Post-hackathon item — stop and cut it per §8.1.

---

## 4. WHAT WE ARE BUILDING — product spec

### 4.1 One-sentence description (for the Devpost form)

*Ghostline is a phone-powered data-verification engine: upload records — or type one in directly — and it calls the numbers via CALL-E, extracts evidence-backed verdicts (MATCH/MISMATCH/UNCLEAR/NO CONTACT), and exports a corrections file. Because "type one in directly" is just a normal input method, anyone can try it on themselves in 90 seconds — no special demo mode.*

### 4.2 The core objects (domain-neutral — do not hardcode healthcare into these)

```jsonc
// Record — a row from an input dataset
{
  "record_id": "provider_001",
  "name": "Northline Family Clinic",
  "phone": "+1XXXXXXXXXX",
  "address": "1420 Oak St, Suite 300",
  "claims": { "accepts_plan": true, "accepting_new_patients": true }
}

// Claim — a testable statement about a record
{
  "claim_id": "accepts_plan",
  "question": "Do you currently accept Northline Health members?",
  "expected_type": "boolean"
}

// ClaimPack — reusable, domain-specific, ~10 lines of config, NOT a new code path
// (healthcare / supplier-crm / community-service — see §4.5)

// Attestation — the output of one resolved claim
{
  "verdict": "MISMATCH",
  "claim_id": "accepts_plan",
  "answer_text": "No, we stopped accepting that plan last month.",
  "evidence_span": "we stopped accepting that plan last month",
  "source_role": "front_desk",       // front_desk | answering_service | call_center | billing_dept | voicemail | ivr_only | unknown
  "confidence": "medium",             // capped by source_role — an answering_service can never reach "high"
  "attested_at": "2026-09-04T10:42:00+05:00",
  "expires_at": "2026-12-03T10:42:00+05:00",
  "call_id": "run_abc123",
  "record_id": "provider_001",
  "evaluation_reason": "Evidence span explicitly denies plan acceptance."
}
```

### 4.3 The four **visible** verdicts (and the richer internal taxonomy underneath)

**User-facing (exactly four, no more):**
- **MATCH** — evidence supports the claim.
- **MISMATCH** — evidence contradicts the claim.
- **UNCLEAR** — call produced information, but it's insufficient/ambiguous/conflicting/unreliable for a binary call. *This is a feature, not an error state — display it as intellectually honest, not broken.*
- **NO CONTACT** — no usable conversation established.

**Internal diagnostic tags (stored, used for the benchmark and failure taxonomy, never surfaced as primary states):**
`AMBIGUOUS`, `CONFLICTING`, `LOW_CONFIDENCE`, `IVR`, `VOICEMAIL`, `BUSY`, `NO_ANSWER`, `CALL_FAILED`, `INVALID_NUMBER`.

### 4.4 The non-negotiable rule: **evidence-span-or-abstain**

A MATCH or MISMATCH verdict **cannot** be produced unless the extractor identifies a verbatim quoted span from the transcript that supports it. No span → automatic **UNCLEAR**. Enforce this in code (a hard assertion in the verdict evaluator), not just in the README. This single rule is what separates Ghostline from every "AI calls people" bot at this hackathon and is your strongest defensible claim under hostile questioning.

Example the extractor must get right:
> Claim: "Currently accepts Northline Health." Transcript: "We take most commercial plans." → **UNCLEAR** — no evidence explicitly names Northline Health.

### 4.5 Claim packs (the reusability proof)

| Pack | Status | Purpose |
|---|---|---|
| **Healthcare — provider directory** | Fully demoed, flagship | Evidence-rich; CMS/AJMC/Senate data behind it |
| **Supplier / CRM contact records** | Fully demoed | Proves domain-neutrality live, in the video |
| **Community service directory** | Written as a ~10-line YAML config in `examples/`, NOT demoed on camera | Proves the fork-and-extend claim to a developer reading the PR without costing build time |

The reusability test to hold every design decision against, verbatim from the harshest review round:
> *"If I fork this tomorrow for supplier records, what do I have to change?"* — The answer must be: **"Add a claim pack."** Not: "rewrite the application."

### 4.6 Core call flow (the runtime path that satisfies "Technical Implementation")

```
Input record + Claim pack
        ↓
Question generation (claim → call goal text)
        ↓
Policy Gate  ── allowlist check · business hours · cadence cap · dry-run flag
        ↓  (blocked → logged, stop here)
CALL-E: plan_call  →  confirm_token
        ↓
CALL-E: run_call
        ↓
Poll: get_call_run  (transcript + activity)
        ↓
Extraction pass (structured, JSON schema, evidence span REQUIRED)
        ↓
Verdict Evaluator (evidence-span-or-abstain enforced here)
        ↓
Attestation written (provenance + expiry)
        ↓
    ┌───┴───┐
Corrections   Derived-call proposal (if a lead was mentioned)
   export         ↓ (requires explicit human approval)
                back to Policy Gate with the NEW number
                (never a number heard mid-transcript, unless approved)
```

### 4.7 One flow, two ways to add records — no separate "Judge Mode," on purpose

Earlier drafts of this doc had a distinct "Judge Mode" — a separate screen with its own rules, just for people trying the product live. **That was a mistake and it's been removed.** A special demo-only path is exactly the kind of thing a sharp judge notices and discounts — "of course it works, it's the mode built to work." The fix is simpler and it's what you proposed:

**There is exactly one way to run a verification, and it has two ways to get records into it:**

1. **Upload a CSV** — the batch path, for real datasets (§4.2's `Record` shape: name, phone, and whatever claim fields the pack needs).
2. **Add a record manually** — a small form on the *same* screen with the same fields (name, phone, claim values or "let AI draft the claim" per §4.12a) for adding one row by hand, right there, no file needed.

That's it. **A judge trying the product doesn't get a "Judge Mode" — they click "Add a record manually," type their own name and their own phone number into the exact same form every other user uses, and hit "Verify."** Ghostline calls the number they just typed, because that's what the form does for anyone, always. No separate rules, no separate rate limits, no separate UI, no separate safety story — one flow, one set of guarantees, for everyone.

This is also a straightforward technical simplification: the "manual entry" path is just a one-row CSV that never touches disk. `core/call_engine.py` and everything downstream of it doesn't know or care whether a record came from a parsed file or a typed form — same object, same code path, same evidence-span-or-abstain rule, same policy gate.

**Do not** let the record-creation form pre-fill or suggest what the "receptionist" should say, and do not badge the manually-entered row as a demo/scenario in the UI. It's a record like any other; the person answering the phone — whoever that is — says whatever they say, and the same extraction/verdict logic resolves it. The most convincing thing that can happen live is someone hedging and getting an honest **UNCLEAR** back — that's the evidence-span-or-abstain rule proving itself unscripted, and it happens automatically now, not because a special mode was designed to produce it.

### 4.8 Live-call safety (non-negotiable, code-enforced, security-tested — applies to every record, every input method, every user, always)

- **Strict dial allowlist:** the only number any verification call can dial is the number present on that record — whether it arrived via CSV row or the manual-entry form — validated as E.164. There is no code path where a number from anywhere else (a transcript, a suggestion, an LLM output) becomes a dial target.
- **No model-generated or transcript-derived number may ever become a dial target.** Call destinations come exclusively from trusted application state: the parsed CSV or the validated form field. This is the core security invariant of the whole project — see §6.3.
- **Session-level rate limit, applied uniformly:** cap live calls per session/IP (e.g., 2–3) regardless of who is using the app or which input method they used. This one rule protects the call budget from any user, not a "judge" specifically — simpler than a mode-specific limit and just as effective.
- **Credit floor:** if the reserved judging-period pool (§1.7) drops to the floor (10), the app stops offering live calls entirely and clearly explains why, falling back to Replay Mode — never spins indefinitely, never appears broken. This applies globally, not to a special mode.
- **International routing must be verified on Day 1** (§8, Day 1 tasks) — likely testers/judges may be Singapore-based; you are Pakistan-based. If SG routing fails, this is a Day-1 finding that reshapes the plan, not a Day-20 surprise.

### 4.9 The corrections file — the actual product outcome

A verdict alone is not a deliverable. Every MISMATCH exports a row someone can act on Monday morning:

```csv
record_id,field,old_value,new_value,verdict,evidence,source,attested_at
provider_001,accepts_plan,true,false,MISMATCH,"we stopped accepting that plan","front_desk","2026-09-04T10:42:00+05:00"
```

Rule: **UNCLEAR records never silently become corrections.** Only evidence-backed MISMATCH rows populate the export. CSV only — do not also build JSON export; one format is sufficient and faster.

### 4.10 Derived calls — the innovation beat

If a call's transcript surfaces a lead ("Sarah handles that now," "we moved to Lakeside"), Ghostline proposes a **new** verification task. It is **never** placed automatically — it requires one explicit human approval click, then re-enters the Policy Gate exactly like any other call. This is the "the answer wrote the next call" moment and the strongest non-obvious feature in the project. Keep it as a thin optional layer on top of the core loop — do not let it complicate the main path.

### 4.11 Expiry — makes the lifecycle real

Every attestation carries `attested_at` and `expires_at`, with the expiry window defined per claim pack (e.g., 90 days for health-plan claims, mirroring the No Surprises Act's own 90-day verification standard — a nice, true, citable parallel). Render expiry visibly (`Attested: Sep 4 · Valid until: Dec 3`). Do not build a three-tier STALE/EXPIRING/VERIFIED status system for the hackathon — one visible date is sufficient; defer tiering post-hackathon.

### 4.12 CHERRIES ON TOP — cheap, high-delight additions layered on the Core (build only after §4.1–4.11 work end-to-end)

Every item below is **Cherry tier** (see the tiering rule in §3): each one reuses data or machinery the Core engine already produces, none require new CALL-E integration surface, and each is individually cuttable per §8.1 without damaging the product. Build them roughly in the order listed — each one is cheaper once the previous one exists.

**(a) Auto-generated claim packs — "any domain" made dynamic, safely.**
Instead of only supporting pre-written claim-pack config files, add one text box: the user types a plain-English description of what they want checked — *"verify these clinics still accept this insurance"* or *"check if these restaurants are still open at these addresses."* An LLM call turns that sentence into a draft claim pack (the list of claims/questions in the exact same format as §4.5's manual packs) and **shows it to the user for approval before any call is placed.** Approving it just saves it as a normal claim-pack file — the Core engine never knows or cares that a human vs. an LLM wrote the config. This is what makes "works for any domain" a demonstrated, dynamic capability instead of an assertion resting on 2–3 hand-written examples, while keeping the safety property that a human always approves the questions before a real phone rings.
> *Guardrail: the generated pack is a proposal, not an executable instruction. Nothing calls anyone until a human clicks approve on the generated questions — same rule as derived calls in §4.10.*

**(b) Auto-suggested recheck interval, generated alongside the pack.**
When a claim pack is generated (auto or manual), the system also proposes a sensible `expires_after` value based on how fast that kind of fact typically goes stale — e.g., ~30 days for "is this restaurant open," ~90 days for "does this office accept this insurance plan" (mirroring the real No Surprises Act 90-day standard already cited in §4.11), ~180 days for "is this the correct company address." User can override the number; the system just needs a sane default. This is a single extra field on the same generation call as (a) — near-zero extra cost, makes the expiry mechanic in §4.11 feel intelligent rather than a flat default.

**(c) Auto-escalation suggestion on low-trust sources.**
If an attestation's `source_role` (§4.2) resolves to something low-trust — `answering_service`, `ivr_only`, `voicemail`, `unknown` — the UI surfaces one line: *"This answer came from an answering service. Want Ghostline to try again during business hours to reach the front desk directly?"* Accepting it is just a normal **derived call** (§4.10) with the same number and the same human-approval gate — no new call logic, just a smarter trigger for the mechanism you're already building. Skip building a separate escalation system; this is a UI suggestion wired to the existing derived-call approve button.

**(d) Plain-English batch summary.**
After a batch of calls finishes, run one more LLM call over the attestations already sitting in the database and produce a single sentence, e.g.: *"12 confirmed, 5 changed, 3 unclear — mostly because staff didn't know the specific plan name."* Display it at the top of the results screen, above the record-by-record list. Cheap because every input to this (verdicts, evidence, evaluation reasons) already exists in the provenance records from §5.5 — this step only summarizes data that's already there, it queries nothing new.

**(e) Audio playback of the call — private, per-call, not published.**
Every completed call already has a recording via CALL-E's `get_call_run` (transcript + activity). Add a play button next to each attestation's evidence span so the person reviewing results can **listen to the actual audio**, not just read the quoted text. Rules for this feature, non-negotiable:
- Playback is visible **only to the person who initiated that specific verification** — whether they added the record via CSV or typed it in manually (§4.7), including someone listening back to a call placed to their own number. It is never embedded in the public demo video, a public results page, or anything shared with third parties, unless the voice belongs to you (your own test lines) or the listener is hearing their own voice back.
- This does **not** relax the kill-list rule against publishing real third-party voices (§3) — it is a private review tool, not a broadcast feature. The distinction is: *who can press play*, not *whether audio exists at all*.
- Where two-party-consent recording laws could apply to a real deployment, document this plainly in `SKILL.md` under the safety section (§6.5/§6.6) — for the hackathon demo, since all real calls go to your own lines or the listener's own number, this is a non-issue, but say so explicitly so a technical judge sees you understood the general case.
- Implementation is small: store the audio reference CALL-E already gives you, add an `<audio>` element next to the transcript pane. No new call-engine work.

**(f) "Explain this verdict" one-click expansion (small polish, do last).**
A button next to any UNCLEAR or MISMATCH verdict that expands `evaluation_reason` (already a stored field per §5.5) into one plain sentence — reusing the exact mechanism from (d) at the single-record level instead of the batch level.

**(g) Duplicate-number guard.**
Before any calls are placed, run a simple group-by on the uploaded CSV: if multiple records share one phone number, flag them in the upload-review screen ("these 3 records all list the same number — one call may resolve all three"). Pure spreadsheet logic on data you already have in memory; zero calls, zero new machinery. Bonus: this doubles as a call-budget saver, since you can resolve 3 claims from 1 dial instead of 3.

**(h) Confidence-colored transcript.**
In the transcript pane, highlight the evidence span itself in a color tied to `confidence` (§4.2) — green for high, amber for medium, red/grey for low or `UNCLEAR`. Every value already exists on the attestation object; this is CSS/UI only, no new data.

**(i) "What changed" diff view on re-verification.**
When a record that already has a prior attestation gets re-verified (its expiry hit, per §4.11), show the old attestation next to the new one, old-value/new-value style, exactly like the corrections file format (§4.9) but rendered as a two-column diff instead of a CSV row. Reuses the corrections logic entirely — it's the same comparison, just triggered on a second pass instead of the first.

**(j) Live call-budget meter.**
A small persistent counter in the console UI: "Calls remaining: 43." You are already tracking this number to enforce the credit floor and the live-call fallback (§4.8, §1.7) — this just renders a value your policy gate already computes. Doubles as a nice, honest visual during the demo and during the judging window.

**(k) Smart call scheduling by timezone.**
Before the queue dials, sort/group records by area code or provided timezone field so calls land during business hours for that number's region automatically, rather than firing in upload order. A sort step on the existing queue, not a new subsystem — but keep this genuinely simple (area-code lookup table, not a full geo service) so it stays Cherry-cheap.

**(l) One-tap "try it yourself" QR code.**
Render a QR code (any small client-side QR library) on the landing page and in the demo video pointing straight at the manual-entry form (§4.7) — the same form everyone uses, just deep-linked to the "add a record manually" tab. Ten minutes of work, disproportionately useful in a video and genuinely useful if judges are watching on a phone.

**(m) Trust score per phone number.**
Once a number has been called more than once (via re-verification or across claim packs), aggregate its attestation history into a small badge: "Verified 3× · always accurate" or "Verified 2× · 1 mismatch." Pure aggregation over attestations already stored in the provenance ledger (§5.5) — no new call logic, and it's a nice preview of what the product looks like once it's been running for months instead of days.

**What NOT to add, even though it would fit this same pattern (Post-hackathon tier — write down, don't build):** multi-language auto-detection of the callee's language, a public shareable link per report, Slack/email alerting on MISMATCH, cross-batch trend analytics, a full geo/timezone service beyond a simple area-code lookup. All reasonable v2 features; all skip-worthy this month per the tiering rule.

**Build order for all thirteen cherries, cheapest/highest-leverage first (stop wherever your schedule tells you to, per §8.1):** (j) budget meter → (g) duplicate-number guard → (l) QR code → (h) confidence coloring → (a) auto-generated claim pack → (e) audio playback → (b) recheck interval → (d) batch summary → (m) trust score → (i) diff view → (c) escalation suggestion → (k) timezone scheduling → (f) explain-this-verdict.

---

## 5. TECHNICAL ARCHITECTURE

### 5.1 Diagram

```
                 ┌─────────────────┐
                 │   Web Console   │  (upload CSV or add a record manually / claims / live-or-replay / transcript / evidence / verdict / correction)
                 └────────┬────────┘
                          │
                 ┌────────▼────────┐
                 │ Ghostline Core  │   (domain-neutral engine)
                 └────────┬────────┘
                          │
          ┌───────────────┼────────────────┐
          │               │                │
    Claim Packs      Verification     Provenance
   (10-line configs)      │           (audit trail)
                   ┌───────▼───────┐
                   │   CALL-E      │
                   │ plan/run/get  │
                   └───────┬───────┘
                          │
                    Transcript
                          │
                  Evidence Engine  (evidence-span-or-abstain)
                          │
              ┌───────────┴───────────┐
              │                       │
           Verdict                 Corrections Export
              │                       │
              └───────────┬───────────┘
                          │
                     Audit Trail
```

The manual-entry path and the CSV path feed the **same engine** through the same `Record` object (§4.2) — there is no parallel implementation to keep in sync, and Replay Mode runs over the same core engine too, just against fixtures instead of live calls. This architectural coherence — one engine, three ways to feed it (CSV, manual entry, replay fixtures) — is itself something a technical judge will notice and credit.

### 5.2 Stack (kept deliberately small)

- **Backend:** FastAPI (Python) or a thin Node/TS service — pick whichever you already know fastest; CALL-E has SDKs for both.
- **Frontend:** minimal web console (Next.js or plain React+Vite). Server-sent events or polling for the live transcript feed.
- **Storage:** SQLite is sufficient for a hackathon-scale ledger; Postgres if you're already comfortable with it. No vector DB, no queue framework beyond a simple serial worker with backoff.
- **CALL-E access:** via MCP (`calle mcp tools`, `calle mcp call <tool>`) or direct SDK/API calls to `plan_call` / `run_call` / `get_call_run`. Use whichever integration path (MCP/SDK/API/CLI/Skill) you can wire fastest and most visibly — "Technical Implementation" rewards genuine, non-trivial runtime usage, not a particular integration method.
- **LLM for extraction/compilation:** Claude (or whichever model you have API access to) with strict JSON-schema structured output for the extractor.

### 5.3 Repository layout (mirrors what the submission repo expects)

```
ghostline/
├── docs/
│   └── MASTER.md                    ← this document
├── skills/
│   └── phone-claim-verifier/
│       ├── SKILL.md
│       ├── references/
│       ├── scripts/
│       ├── examples/
│       │   ├── healthcare-pack.yaml
│       │   ├── supplier-crm-pack.yaml
│       │   └── community-service-pack.yaml   ← config-only, not demoed
│       └── tests/
├── core/
│   ├── claim_pack.py / .ts
│   ├── claim_pack_generator.py / .ts  (§4.12a — plain-English → draft pack, human-approve gate)
│   ├── call_engine.py / .ts          (plan_call → run_call → get_call_run wrapper)
│   ├── extractor.py / .ts            (evidence-span-or-abstain enforced here)
│   ├── verdict.py / .ts
│   ├── corrections.py / .ts
│   ├── summarizer.py / .ts            (§4.12d/f — batch + per-record plain-English summaries)
│   ├── cherries.py / .ts              (§4.12g/i/j/k/m — dup-guard, diff view, budget meter, tz sort, trust score: small pure-function helpers, no new external deps)
│   └── policy_gate.py / .ts           (allowlist, cadence cap, dry-run, business hours)
├── console/                          (web app: CSV upload + manual-entry form / live view / audio playback §4.12e / QR code §4.12l)
├── replay/
│   └── fixtures/                     (9 canonical transcripts, §5.7)
├── benchmark/
│   └── results.json                  (generated, never hand-written — §5.9)
├── FEEDBACK.md                       (running log for Most Valuable Feedback — §7.4)
└── README.md
```

### 5.4 Verdict enum (code-level)

```python
class Verdict(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    UNCLEAR = "UNCLEAR"
    NO_CONTACT = "NO_CONTACT"

class DiagnosticTag(str, Enum):   # internal only, never primary UI state
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTING = "CONFLICTING"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    IVR = "IVR"
    VOICEMAIL = "VOICEMAIL"
    BUSY = "BUSY"
    NO_ANSWER = "NO_ANSWER"
    CALL_FAILED = "CALL_FAILED"
    INVALID_NUMBER = "INVALID_NUMBER"
```

### 5.5 Provenance model (every verdict must answer "why?" in seconds)

Minimum fields per attestation: `record_id`, `claim_id`, `call_id`, `source_role`, `transcript_reference`, `evidence_span`, `attested_at`, `expires_at`, `verdict`, `evaluation_reason`.

### 5.6 Failure handling — every call reaches a terminal state, nothing spins forever

Explicit states to design for: no answer, busy, voicemail, IVR, call failure, invalid number, ambiguous answer, contradictory answer, missing evidence, transcript unavailable, timeout, cancellation, rate limit, exhausted call budget. On budget exhaustion or floor breach: **graceful fallback to Replay Mode**, never a broken UI.

### 5.7 Replay harness — build this *before* the live call engine

Nine fixture transcripts, hand-written, covering: MATCH, MISMATCH, UNCLEAR, NO_CONTACT, AMBIGUOUS, CONTRADICTORY, VOICEMAIL, IVR, NO_ANSWER. All console and extraction development runs against these first. This is what makes §1.7's tight call budget survivable — you should be able to demo 90% of the product having spent under 10 live calls in development.

### 5.8 Dry-run — the default

```
$ ghostline verify providers.csv --dry-run
10 records loaded
10 claims generated
0 live calls
10 planned calls
```
Only an explicit `--live` flag (or equivalent console toggle) consumes real CALL-E calls. Document this prominently in `SKILL.md` — dry-run-by-default is exactly the kind of safety-by-default detail the CALL-E team's own repo README asks contributors for (see the actual `awesome-phone-call-agents` safety rules, §6.5).

### 5.9 Reliability benchmark — generate it, don't write it

```jsonc
// benchmark/results.json — generated by scripts/run_benchmark.py, never hand-edited
{
  "n_calls": 41,
  "human_agreement_rate": 0.93,
  "abstention_rate": 0.11,
  "failure_taxonomy": {
    "IVR": 3, "VOICEMAIL": 2, "AMBIGUOUS_MISCLASSIFIED": 4
  },
  "generated_at": "2026-09-05T14:20:00+05:00"
}
```
The console UI **reads this file** to render the one-line stat shown in the demo and on the landing page. This makes it structurally impossible to display a number you didn't measure — the single most important integrity guardrail in the whole project, given the project's thesis is evidentiary honesty. Whatever the real numbers are — even if agreement is 78%, not 93% — display them and explain the failure taxonomy. Honest imperfection scores higher with a technical judge than an unexplained high number.

### 5.10 Testing (scoped — do not over-build)

**Unit tests (the ones that matter, ~8 total):** evidence-span enforcement (no span → forced UNCLEAR), dial-allowlist enforcement, expiry calculation, corrections export excludes UNCLEAR, rate-limit cap, claim-pack loader (new pack = new file, zero code change), verdict-from-fixture correctness on all 9 replay fixtures, prompt-injection resistance (transcript saying "call this other number" must not alter the dial target).

**Integration smoke tests:** `plan_call` → `run_call` → `get_call_run` round-trip against one real number; cancellation of an in-flight job.

**Do not build:** a large multi-layer security test suite, exhaustive integration coverage, or anything a judge won't plausibly open. Meaningful and present beats exhaustive and unread.

---

## 6. SAFETY, PRIVACY, AND LEGAL COMPLIANCE — mapped to actual rule clauses

### 6.1 IP / trademark / publicity — Official Rules, Submission Requirements + §7 + §9

- **No real clinic, insurer, plan, or company names/logos anywhere** — screen, demo, README. Use `Northline Health`, `Northline Family Clinic`, `Harbor Supply Co.`, `Community Bridge Services`.
- **No copyrighted music** in the video unless you hold a license.
- **No real people's voices published without written consent** (Rules §7: entrants warrant content doesn't violate "privacy and publicity rights... unless entrant is the owner of such rights or has permission"). Practical fix: demo calls go to your **own second phone/test line**, labelled on screen as such (*"calling a test line we operate"*) — zero consent friction, zero privacy exposure, and arguably a stronger, more honest story than a scripted consented panel. When someone else tries the app themselves and types in their own number (§4.7), that's inherently their own consent for their own call.
- **Prefer transcript + waveform over raw playback of any voice you don't own outright.**

### 6.2 "Financial or Preferential Support" clause (Official Rules §4)

Confirm and be ready to state: this project was not developed with funding, investment, contract work, or a commercial license from AIRUDDER/CALL-E prior to submission. It wasn't — just be aware this clause exists and don't accept any offer of paid support from the sponsor mid-build without checking this clause first.

### 6.3 The core security invariant (state this explicitly in `SKILL.md` and the Devpost description — it's a strong technical-implementation signal)

> **No model-generated or transcript-derived text may ever directly control the destination of a phone call.** Phone numbers dialed by Ghostline originate exclusively from trusted application state: a parsed CSV row, or a validated form field on the exact same manual-entry screen every user sees (§4.7) — there is no separate "tester" input path with different rules. A receptionist saying "call this other number instead" is data, not an instruction. A derived-call proposal surfaces a *suggested* new number for **human approval**; approval, not the transcript, authorizes the dial.

### 6.4 PHI / sensitive-data leakage

The agent never asks for or should request patient/personal information. A receptionist may volunteer it anyway. Run a redaction pass on stored transcripts before persistence; keep retention short (document the window in `SKILL.md`); state this plainly in the console UI.

### 6.5 The upstream repo's own safety rules apply to your PR — follow them literally

From `awesome-phone-call-agents/skills/*/references/safety.md` and the repo README (already fetched and summarized in your research):
- Require explicit user intent before setup or execution.
- Mask phone numbers in user-facing summaries; use reserved/fictional numbers in docs (e.g., `+15550101234`).
- Never call any number except the configured E.164 number.
- Never modify a user-provided goal/message except for safety-preserving formatting.
- Never create duplicate scheduled jobs or hidden recurring schedules.
- Never expose API keys, OAuth tokens, session cookies, or provider credentials — anywhere, including screenshots in the video.
- If auth is missing/ambiguous, **skip the call, don't guess.**
- Every setup summary must include cancellation/update instructions.

### 6.6 Telephony & disclosure

Every real call opens with a disclosed AI identity and stated purpose before any question ("automated verification call, three quick questions, no patient information requested"). Respect callee business hours; one call per number per day cap; honor any "don't call again" immediately; log it.

---

## 7. POSITIONING & JUDGE PSYCHOLOGY

### 7.1 Which prize to aim for

Aim the copy at **Most Practical Use Case ($4,000)**. It is a real, deployable, boring-but-critical workflow with clear ROI (corrections file, compliance angle). **Most Innovative ($3,000)** is credible upside from the derived-call feature and the lifecycle framing, but a project can only win one prize — don't dilute the pitch trying to be both. If judges see it as more innovative than practical, that's fine; you don't control the lane, only the strength of the case.

### 7.2 Frame for these specific judges

AIRUDDER is an enterprise voice-AI company. A pitch that reads as "American Medicare compliance software" is narrower and more foreign to this panel than it needs to be. Lead with the **universal frame**:

> *"Every company has a database that's quietly rotting — CRM contacts, supplier records, service directories, member listings. Ghostline turns the phone from an outreach channel into a data source that keeps that database honest."*

Healthcare is the flagship **evidence**, not the product's **identity**. Say "phone-verified data hygiene" before you say "healthcare directories."

### 7.3 The three questions to rehearse until they're one sentence each

1. *"Your app calls me and I say something wrong. What does the product claim it learned?"* → **"An attestation with provenance, not a fact — a timestamped record of what a specific source said, not a truth claim."**
2. *"How many real calls are behind the numbers in this video?"* → Have the exact figure from `benchmark/results.json` ready, unhesitatingly.
3. *"If I fork this for supplier records tomorrow, what do I write?"* → **"A ten-line claim pack. The engine doesn't change."**

### 7.4 Most Valuable Feedback ($200 × 5) — do this in parallel, not as an afterthought

Keep `FEEDBACK.md` open from Day 1. Log every real friction point as you hit it: auth token TTL behavior, `get_call_run` polling semantics, transcript structure quirks, cancellation edge cases, IVR/voicemail handling gaps, E.164/international routing issues, CLI error messages that were unclear, anything about the docs that cost you time. Submit via the official CALL-E Feedback Survey **during the Feedback Period (through Sep 18, 2026)** — note this is *after* your Sep 14 submission deadline, so you have a few extra days to polish this specifically. Highest expected value per hour of effort in the entire contest, and it's scored separately from your project — pure additive upside.

---

## 8. THE BUILD PLAN — day-by-day, risk-first sequencing

**Sequencing principle: retire the biggest risk first, not the "logical" architectural order.** The biggest risk is not "will the engine be elegant" — it's "will a Singapore-based judge's phone actually ring in October." Test that risk on Day 1, not Day 20.

Dates below assume a start of **Aug 18, 2026** (today) against the **Sep 14, 8:45 PM GMT+5** deadline — **27 days**. Re-anchor these dates to whatever day you actually start.

| Day(s) | Work | Kill-gate / what must be true to proceed |
|---|---|---|
| **Day 1 (Aug 18)** | Install `calle` skill/CLI (`npx -y skills add https://github.com/CALLE-AI/call-e-integrations --skill calle -g`), `npm install -g @call-e/cli`, `calle auth login`. Run `calle mcp tools` — confirm `plan_call`/`run_call`/`get_call_run` present. Place **one call to your own phone**. Place **one call to an international/Singapore-region mobile number** if you can arrange one. **Submit the +200-call request form immediately.** Start `FEEDBACK.md`. | International (or best-available non-local) routing confirmed working, or the manual-entry input path's validation/messaging changes today, not later |
| **Days 2–3** | One-page architecture note (data model + call flow + repo layout — condense §4–5 of this doc). Build `core/claim_pack.py`: domain-neutral loader, healthcare pack as first config. `ghostline verify --dry-run` prints planned calls, zero live calls. | `--dry-run` works cleanly on a 10-row fixture CSV |
| **Days 4–6** | Call engine: `policy_gate` → `plan_call` → `run_call` → poll `get_call_run` → transcript. Cancellation + retries + terminal states (§5.6). **Replay harness + all 9 fixtures written in parallel, before burning more live calls.** | 3 real calls end-to-end, cleanly logged |
| **Days 7–9** | Verification layer: extractor with evidence-span-or-abstain enforced in code, 4-verdict evaluator, provenance record, expiry calc, `corrections.csv` export. 8 unit tests from §5.10 passing. | The "we take most commercial plans" fixture correctly returns UNCLEAR, not a guess |
| **Days 10–12** | Console: upload → claims render → live/replay toggle → transcript pane → evidence pane → verdict → correction download. One screen, three panes (record / live call / resolution) per the ideal layout in §4 research. | A stranger understands the screen without narration |
| **Days 13–15** | **Manual-entry input path + global live-call safety**: build the "add a record manually" form (§4.7) as a second way into the exact same flow as CSV upload, E.164 input validation, allowlist enforcement (number can only be the one just typed or uploaded), session-level rate cap (2–3 live calls), credit-floor fallback to Replay-only, NO_CONTACT path for no-answer, health-check endpoint, deploy hosted. | A friend in a different country can open the app, type their own number into the same form, get a real call, and see a verdict resolve — no special mode involved |
| **Days 16–17** | Derived-call feature: lead detection in transcript → proposal card → human approval → re-enters policy gate with the new number. | One call's answer visibly authors the next task |
| **Day 18** | Supplier/CRM claim pack, fully demoed. Community-service pack as a 10-line YAML in `examples/`, config-only, not demoed. | Pack swap requires zero core-engine code changes |
| **Day 18.5 (half day, only if on schedule)** | **Cherries, §4.12 — 13 total, build in the ordered list given there, stop the moment your slack runs out.** Cheapest/highest-leverage first: budget meter → duplicate-number guard → QR code → confidence coloring → auto-generated claim pack → audio playback → recheck interval → batch summary → trust score → diff view → escalation suggestion → timezone scheduling → explain-this-verdict. | Each cherry is independently demoable; none touches the call engine or policy gate |
| **Day 19** | Reliability benchmark: ~40–50 real calls (own test lines + fixtures where live calls aren't warranted), human-labelled, `scripts/run_benchmark.py` generates `benchmark/results.json`. UI reads from this file, never hardcodes it. | The file exists with real numbers, whatever they are |
| **Days 20–21** | **PR finalized** (should already be open as a draft since ~Day 14 — see §9). `python3 scripts/validate_repository.py` passes. `SKILL.md` complete with install/config/dry-run/live/claim-packs/CALL-E-orchestration/polling/retries/cancellation/safety/allowlist/evidence-span/provenance/expiry/replay/testing/failure-modes sections. Correct branch name per `docs/git-naming-conventions.md`. Correct Contribution Area folder. | A stranger maintainer could plausibly merge this PR as-is |
| **Day 22** | Video recording (§10). Fictional data only, no trademarks, no unreleased voices, no copyrighted music. Target 2:35–2:45 (under the 3:00 hard cap — judges aren't required to watch past 3:00). | Video ≤ 3:00, every rule in §6.1 respected |
| **Day 23** | Devpost description written with the four judging-criteria names as literal H2 headers (§10.4). Submission form filled: PR URL, video URL (YouTube/Vimeo, public), CALL-E account email, optional hosted-app URL. | Every required field from Official Rules §"Submission Requirements" present |
| **Day 24 (Sep 12)** | **Submit — two days of margin before the deadline.** | Submission visible on Devpost as complete, not draft |
| **Days 25–26** | Buffer. Confirm hosted app health-check green, credit counter shows the reserved judging-period pool untouched. Watch Discord/forum for any late rule clarifications. | App up, credits intact |
| **Day 27 (Sep 14, 8:45 PM GMT+5)** | Hard deadline passes. | — |
| **Through Sep 18** | Submit CALL-E Feedback Survey from the accumulated `FEEDBACK.md`. | Survey submitted within the Feedback Period |
| **Sep 30 – Oct 13** | **Judging Period — the app must survive unattended.** Do not tear down infrastructure. Monitor uptime and the reserved credit pool daily if possible. | App never returns a dead page to a judge |
| **~Oct 19** | Winners announced. If selected, respond promptly to the winner-affidavit request — Rules give you only 10 business days to return Required Forms (W-9/W-8BEN etc.) or risk delayed/forfeited prize. | — |

### 8.1 Cut order if the schedule slips (in this exact order, never out of order)

0. **Cut Cherries first, in reverse of the build order given in §4.12** (last-built is first-cut). None of them are load-bearing; none should ever cost you a day the Core needs.
1. Reduce benchmark size (40 real calls is fine; 25 is a floor, not below).
2. Reduce derived-call sophistication (a single-hop proposal is enough; don't chain multiple derived calls).
3. Drop the supplier/CRM pack's on-camera demo — keep it as a written config only, same as the community pack.

**Never cut, under any schedule pressure:** the manual-entry input path (§4.7), evidence-span-or-abstain, corrections export, the dial allowlist, Replay Mode, PR quality, a working hosted experience that survives the judging window.

---

## 9. THE REPOSITORY PR — a first-class deliverable, not paperwork

- **Open a draft PR by ~Day 14**, not on submission day. A visible, evolving PR with real commits over two weeks reads as genuine effort; a PR opened hours before the deadline reads as an afterthought regardless of code quality.
- **Correct Contribution Area:** `skills/phone-claim-verifier/` per the `awesome-phone-call-agents` README table (Agent Skills row). Optionally also list under `apps/` if you want the functional-app angle explicitly covered too.
- **Follow `docs/git-naming-conventions.md`** in that repo for branch names, commit messages, and PR title — verified, not guessed.
- **Run `python3 scripts/validate_repository.py`** before every push that matters; it validates required files, English-only content, skill frontmatter, and reference-skill acceptance text.
- **`SKILL.md` must be genuinely complete**, following the skill folder template (`SKILL.md`, `references/`, `scripts/`, `assets/`) and covering every item the repo's own contribution guidance asks for: installation, configuration, dry-run, live execution, claim packs, CALL-E orchestration, polling, retries, cancellation, safety, dial allowlist, evidence-span requirement, provenance, expiry, replay, testing, failure modes.
- **No secrets, no dead code, no unexplained magic constants, no fabricated benchmark numbers** — a reviewer who spots one fabricated number will assume the rest is unreliable too.

---

## 10. THE DEMO VIDEO — hard constraints + shot list

### 10.1 Hard constraints (violating any of these is a Rules violation, not a style choice)

- **Under 3:00.** Judges are not required to watch beyond 3:00 — every second past that is wasted effort.
- **Must show the project functioning on its intended platform** (the hosted console / CLI / whatever you specify as the target).
- **Public on YouTube or Vimeo**, link on the Devpost form.
- **No third-party trademarks.** No real clinic/insurer/plan names, no real brand logos.
- **No copyrighted music** unless licensed.
- **English**, or an English translation provided alongside.

### 10.2 Shot list (target 2:35–2:45)

| Time | Beat |
|---|---|
| 0:00–0:12 | Landing page with the lifecycle line on screen: *"asserted → verified → evidenced → corrected → expired → re-verified."* *"The URL is on screen right now — Ghostline can call you. Try it yourself."* |
| 0:12–0:22 | Fictional record on screen: `Northline Family Clinic · accepts_plan: TRUE`. *"Nobody's checked this in 18 months."* |
| 0:22–1:05 | Real call to your own labelled test line. Transcript streams live. Verdict chips resolve. |
| 1:05–1:25 | MISMATCH → evidence span highlighted → `front_desk · attested 10:42 · expires in 90 days`. *"Ghostline doesn't claim truth. It claims someone said this, at this time, and here are their exact words."* |
| 1:25–1:40 | **UNCLEAR case** — a hedged answer, abstention with a stated reason. Don't cut this; it's the credibility beat. |
| 1:40–1:55 | `corrections.csv` downloads and opens; TRUE → FALSE with the quote in a visible column. |
| 1:55–2:12 | Derived call: transcript mentions "Sarah handles that now" → proposal card → approve → second call. *"The answer wrote the next call."* |
| 2:12–2:22 | **If cherries (a)+(e) are built:** type a plain-English request — *"verify these restaurants are still open"* — pack auto-generates, human approves it, then click play on the evidence audio from an earlier call. *"Same engine, any domain you can describe — and you can always listen back to what was actually said."* If cherries aren't ready in time, skip straight to the pack-swap beat below; this slot is optional. |
| 2:22–2:32 | Pack swap: supplier/CRM record, same engine, one config file. *"Same engine. Different claim pack."* |
| 2:32–2:40 | Lifecycle diagram, 3 seconds. Close: *"Ghostline doesn't maintain your database. It tells you when reality has moved on — and it's still online right now. Call yourself."* |

A persistent lower-third from ~1:05 onward showing the live `benchmark/results.json` stat (e.g., "41 real calls · 93% human agreement · 11% abstained") reads as ambient rigor without spending a dedicated segment on it.

### 10.3 What must never appear on screen

Real clinic/insurer/plan names or logos; any API key, OAuth token, session cookie, or credential (even briefly in a terminal pane); an unreleased human voice; copyrighted music; anything that could be read as a real endorsement by a real company.

### 10.4 Devpost description — literal structure

Use the four judging criteria as literal `##` headers, in their official order, so scoring is frictionless for the reader:

```markdown
## Real World Impact
[CMS/AJMC/Senate Finance stats, who buys it, what changes Monday, why worth building further]

## Quality of the Idea
[The lifecycle primitive, attestation-vs-truth distinction, evidence-span-or-abstain, claim-pack extensibility, derived calls]

## Technical Implementation
[plan_call → run_call → get_call_run flow, allowlist + injection defense, retries, cancellation,
 replay harness, provenance, expiry, tests, benchmark — link the PR and SKILL.md directly]

## Product Experience & Demo
[Replay Mode, the manual-entry path with 3-step "try it yourself" instructions, corrections file, hosted URL, safety statement:
 "A verification only ever calls the number on the record you added or uploaded — never any other number."]
```

---

## 11. RISK REGISTER

| Risk | Likelihood | Mitigation | Owner action |
|---|---|---|---|
| International call routing fails for judge's likely region | Medium | Test Day 1; redesign the manual-entry form's input validation/messaging if it fails | Day 1, non-negotiable |
| Call credits exhausted before/during judging | Medium | Hard-coded credit floor + Replay fallback; reserve 80–90 calls untouched; request +200 immediately | Ongoing, code-enforced |
| Judge tests the hosted app weeks after submission and it's down | Medium | Health-check endpoint; don't tear down infra; monitor during Sep 30–Oct 13 | Days 25–26 + ongoing |
| Fabricated or unmeasured numbers slip into the demo/UI | Low if disciplined | `benchmark/results.json` is generated, never hand-written; UI reads from file only | Day 19 design constraint |
| Real voice/brand exposure creates a Rules violation | Low if disciplined | Fictional names only; own test lines; transcript-first evidence display | Baked into every screen from Day 1 |
| PR is rushed/thin, hurting Technical Implementation score | Medium if left to the end | Draft PR open by Day 14; `validate_repository.py` in CI/pre-push habit | Days 13–21 |
| Scope creep (six verdicts, three fully-demoed packs, statistics, registry) eats the schedule | High without discipline | §3 kill list; §8.1 cut order; re-read this doc before adding anything not in it | Continuous |
| Prompt injection via transcript changes a dial target | Low if code-enforced | Dial destinations only from trusted application state, tested explicitly (§5.10) | Days 4–6, 13–15 |
| Winner-affidavit paperwork deadline missed post-announcement | Low | 10 business days to return Required Forms — calendar this now if you win | Post-Oct 19, if applicable |

---

## 12. GLOSSARY — terms used consistently across this doc

- **Record** — one row of the input dataset (e.g., a provider listing).
- **Claim** — a single testable statement about a record.
- **Claim Pack** — a reusable, domain-specific bundle of claims/questions; the engine's extension point.
- **Attestation** — the structured output of one resolved claim: verdict + evidence + provenance + expiry.
- **Evidence span** — the verbatim quoted transcript fragment supporting a verdict; mandatory for MATCH/MISMATCH.
- **Source role** — who answered (front_desk / answering_service / call_center / billing_dept / voicemail / ivr_only / unknown); caps confidence.
- **Verdict** — one of MATCH / MISMATCH / UNCLEAR / NO CONTACT (user-facing); richer diagnostic tags exist internally.
- **Corrections file** — the CSV export of evidence-backed MISMATCH rows; the actual actionable deliverable.
- **Derived call** — a new verification task proposed from a lead mentioned mid-transcript; requires human approval.
- **Manual-entry path** — the second way to add a record, alongside CSV upload: typing name/phone/claims directly into the same form the CSV path feeds into. This is how anyone, including a judge, tries the real product on themselves — no separate "demo mode" exists.
- **Replay Mode** — default-safe, zero-live-call exploration of the full product via fixture transcripts.
- **Policy Gate** — the allowlist/business-hours/cadence/dry-run check every call must pass before dialing, regardless of whether the record came from a CSV or the manual-entry form.
- **Lifecycle** — asserted → verified → evidenced → corrected → expired → re-verified; the core product statement.
- **Cherry (tier)** — a feature that's cheap, reuses Core data/machinery, and is individually cuttable without damaging the product (§3, §4.12). Never blocks Core work; always cut before Core is touched.
- **Auto-generated claim pack** — a claim pack drafted by an LLM from a plain-English request, always shown to a human for approval before any call is placed (§4.12a).

---

## 13. FINAL PRE-FLIGHT CHECKLIST (run this the night before Sep 14)

- [ ] PR open, `validate_repository.py` green, correct branch/folder, `SKILL.md` complete
- [ ] Hosted console live, health-check green, credit counter shows reserved pool intact
- [ ] Video ≤ 3:00, public on YouTube/Vimeo, no trademarks/logos/unreleased voices/copyrighted music
- [ ] `benchmark/results.json` exists, was generated (not hand-written), and matches what's shown in the video/UI
- [ ] Devpost description has the four criteria as literal headers, links PR + video + hosted URL
- [ ] CALL-E account email provided on the submission form
- [ ] The manual-entry path tested end-to-end by someone who is not you, ideally from a different country/network — using the exact same form and flow a normal user would
- [ ] Dial allowlist security test passes (transcript injection attempt does not redirect the call)
- [ ] `FEEDBACK.md` populated and ready to convert into the Feedback Survey submission
- [ ] No real clinic/insurer/company names anywhere in the repo, video, or Devpost text
- [ ] If any Cherries (§4.12) shipped: audio playback confirmed private-only (never in the public video/report unless it's your own voice or the listener's own), auto-generated claim packs confirmed to require human approval before any call
- [ ] Submitted at least a few hours before 8:45 PM GMT+5 on Sep 14 — not at the wire

---

*End of Master Document. Update in place as the project evolves; do not fork multiple versions of this file.*
