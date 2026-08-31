# GHOSTLINE — Hackathon Analysis (verified against official page + Official Rules, 2026-08-31)

Cross-check of master doc §1 against the live Devpost page, the Official Rules, and the
Additional Calls Request Form. **Master doc §1 is substantially accurate.** Deltas below.

---

## 1. Dates — CONFIRMED, with one clarification

| Event | Official Rules (SGT = GMT+8) | Your local (PKT = GMT+5) | Master doc §1.1 |
|---|---|---|---|
| Submission deadline | **Sep 14, 2026, 11:45 PM SGT** | **Sep 14, 8:45 PM PKT** | 8:45 PM GMT+5 ✅ |
| Feedback deadline | Sep 18, 11:45 PM SGT | Sep 18, 8:45 PM PKT | "Sep 18, 11:45 PM SGT" ✅ |
| Judging | Sep 30, 10:00 AM SGT → Oct 13, 5:00 PM SGT | Sep 30, 7:00 AM → Oct 13, 2:00 PM PKT | says 6:00 AM start — **off by 1h**, trivial |
| Winners | ~Oct 19, 2:00 PM SGT | ~Oct 19, 11:00 AM PKT | 11:00 AM ✅ |

**Clarification of the master doc §1.1 warning:** master doc says the deadline is "8:45 PM GMT+5,
not 11:45 AM/PM SGT." In fact **11:45 PM SGT is correct and equals 8:45 PM PKT** — they are the
same instant. The actionable local time (8:45 PM Sep 14, Pakistan time) in the master doc is
right; only its claim that the SGT figure was wrong is itself mistaken. **Plan against 8:45 PM
PKT Sep 14; submit Sep 12.** Page banner also shows "8:45pm GMT+5" and "15 days to deadline".

## 2. Binding integration requirement — ⚠️ DELTA (affects Stage One pass/fail)

Marketing copy says "SDK, API, MCP, CLI, or SKILL." But the **binding Project Requirements
clause** says:

> "a functional software application that uses CALL-E's **API or SDKs for Python/TypeScript**,
> or integrates **CALL-E Skill or MCP**"

**CLI is not in the binding requirement.** Stage One checks the project "reasonably applies
CALL-E APIs, SDKs, MCP, or Skill integrations" — CLI omitted there too.

**Action:** the runtime integration that judges see "imported and actually called at runtime"
must be **the Python SDK, the API, MCP, or a Skill** — not CLI-only. Given Python/FastAPI:
→ **primary = CALL-E Python SDK** (cleanest "imported and called at runtime" story)
→ **PR contribution = Agent Skill** in `awesome-phone-call-agents`
→ CLI is fine as a dev convenience, but never the sole integration path.
Updates master doc §1.6 / §5.2 (which left CLI as an equal option). → [DECISIONS.md](../planning/DECISIONS.md) O-002.

## 3. CALL-E API surface — ⚠️ VERIFY BEFORE CODING

Master doc §1.6 asserts the runtime tools are `plan_call → run_call → get_call_run`. But the
Aug 27 Build Session and quickstart describe CALL-E in terms of **"goals"** — "define a goal,
provide context, trigger a real phone interaction, get back structured results," one-shot
goals vs. long-running task goals, and "improving a goal from call history."

**The master doc's tool names may be approximate/outdated.** Do not hardcode against them.
**Day-1 task:** read `docs.heycall-e.com/quickstart` + `#/sdks` + `#api-reference` and the
Build Session (youtu.be/qzHIFuZkCik) and record the **actual** SDK/MCP method names and the
call lifecycle in [CALL_E_INTEGRATION.md](CALL_E_INTEGRATION.md). Then reconcile master doc §4.6 / §5.

## 4. Contribution area / folder — VERIFY

Master doc §1.5 assumes `skills/phone-claim-verifier/`. The page says "Follow the instructions
under the README to submit your pull request to the correct Contribution Area." We have **not
read that README**. Day-1: read `github.com/CALLE-AI/awesome-phone-call-agents` README +
`docs/git-naming-conventions.md` + `scripts/validate_repository.py`, and confirm the exact
folder, frontmatter, and branch-name rules. Also list under `apps/` if the README supports it.

## 5. Additional Calls Request Form — ⚠️ PREREQUISITES + URGENCY (new detail)

Master doc §1.7 says "submit the form the moment you finish reading this doc. Do not wait."
The form adds constraints the master doc didn't have:

- **You must have logged into CALL-E at least once** before they can add credits (the form has
  a hard confirmation checkbox). → Sign up + `calle auth login` **first**.
- **You must be officially registered + eligible for the hackathon** (needs Devpost username).
- **First-come, first-served, while supplies last.** Not guaranteed. Speed matters.
- Form's own cutoff: **Sep 14, 12:00 PM SGT** (9:00 AM PKT) — but submit *now*, not near it.
- Processing: **1–5 business days.** From Aug 31, worst case lands ~Sep 5–7.
- For >200 later: must have used **≥80%** of current calls and show genuine building; resubmit.

**Correct order today:** (1) Join hackathon on Devpost → note username. (2) Install + create
CALL-E account, `calle auth login`, `calle auth status`. (3) Submit the Additional Calls form
immediately. (4) Test calls.

## 6. Everything else in master doc §1 — CONFIRMED

- Two-repo split (`call-e-integrations` = setup, `awesome-phone-call-agents` = submission) ✅
- Sponsor: AIRUDDER Pte Ltd, **182 Cecil Street, Singapore 069547** → SG-based judges very
  likely → **international/SG call-routing test on Day 1 is non-negotiable** ✅ (master doc §4.8)
- Stage-One pass/fail gate, then 4 equally-weighted criteria (25% each) ✅
- Tie-break order: Real World Impact → Quality of Idea → Technical Implementation → Product
  Experience → judge vote ✅ (our strongest axis is also the first tiebreaker)
- One project wins one prize; Feedback prize ($200×5 + 10k credits) is separate, per-individual,
  stacks — but feedback-only entrants get nothing else ✅
- 20 free calls automatic; +200 by form ✅
- Video < 3:00, YouTube/Vimeo public, no third-party trademarks / no copyrighted music ✅
- English or provide translation ✅
- Judges may test the live app free/unrestricted **through Oct 13**, but are not required to ✅
- "Newly created or significantly updated during the Submission Period" — Ghostline is new;
  **state this explicitly in the Devpost writeup** ✅
- Winner affidavit / W-8BEN: **10 business days** to return Required Forms — calendar if we win ✅
- 2,614 participants registered → crowded field; differentiation matters ✅

## 7. Prizes (confirmed)

| Prize | Cash | Extras | Qty |
|---|---|---|---|
| Most Practical Use Case | $4,000 | CALL-E team meeting, blog feature, 20k credits (~$200) | 1 |
| Most Innovative Use Case | $3,000 | same | 1 |
| Honorable Mention | $1,000 | meeting, blog, 10k credits (~$100) | 2 |
| Most Valuable Feedback | $200 | 10k credits (~$100) | 5 |

Target: **Most Practical** (master doc §7.1). Innovative is upside; don't dilute the pitch.

## 8. Net change to our plan

1. **Integration decision firmed:** CALL-E **Python SDK** as primary runtime path + Agent Skill
   for the PR. (Was "MCP/SDK/API/CLI, pick fastest.")
2. **Day-1 additional-calls form** now has an explicit prerequisite chain (Devpost register →
   CALL-E login → form) and first-come urgency.
3. **Two Day-1 verification tasks added:** real CALL-E SDK/MCP method names + lifecycle; and the
   `awesome-phone-call-agents` README contribution rules. Both feed doc reconciliation.
4. No change to idea, scope, thesis, kill-list, or timeline.
