# GHOSTLINE — Competitive Strategy

**Date:** 2026-08-31 · **Owner:** single entrant · **Based on:** [`GHOSTLINE_MASTER_DOC.md`](../masterdocs/GHOSTLINE_MASTER_DOC.md)
This is the condensed, decision-ready strategy. The master doc is the full spec; this is what we optimise for and what we cut.

---

## Core problem

Every organisation has a database that is quietly rotting — CRM contacts, supplier records, provider directories, service listings. The facts that rot ("is this office still here, do they still accept this plan, is this still the contact person") **do not live in any API**. They live in a human's head and decay constantly. No scrape, no portal, no chatbot can retrieve them. Only a phone call can.

Flagship evidence domain: US health-plan provider directories — CMS found **48.74%** of Medicare Advantage directory locations had at least one inaccuracy; Senate Finance secret-shopper study found an **18%** booking-success rate; AJMC found **40.3%** of known errors persisted ~540 days; CAQH puts directory upkeep at **$2.76B/year**. The REAL Health Providers Act (signed Feb 2026) makes measuring directory accuracy a federal obligation.

## Target user

Primary buyer framing for judges: **any ops/data team with a phone-reachable database that must stay accurate** — health-plan network teams, supplier/procurement, sales ops, 211/community-service directories. Healthcare is the *evidence case*, not the product identity. Lead with "phone-verified data hygiene," then name healthcare.

## Proposed solution

Give Ghostline a table of records + a claim pack. It calls each number via CALL-E, asks the questions, extracts **what the human actually said with a mandatory verbatim evidence span**, and returns **MATCH / MISMATCH / UNCLEAR / NO CONTACT** — never a guess it can't support — plus a `corrections.csv` someone can act on Monday morning. Attestations carry provenance + an expiry clock; expiry triggers re-verification.

## Core thesis (one line)

> **Ghostline doesn't claim truth. It creates a timestamped, evidence-backed record of what a specific human source said — and tells you when reality has moved on.**

Alt phrasing for the video: *"The phone stops being an outreach channel and becomes a data source that keeps your database honest."*

## The unique mechanism (what makes us different)

**Evidence-span-or-abstain, enforced in code.** A MATCH/MISMATCH verdict is *impossible* to produce unless the extractor identifies a verbatim quoted span from the transcript that supports it. No span → forced UNCLEAR. This is a hard assertion in the verdict evaluator, not a README promise. It is the single defensible claim under hostile questioning and the thing that separates Ghostline from every "AI that calls people" bot at this hackathon.

Supporting mechanisms: attestation-vs-truth data model with provenance; source-role confidence capping (an answering service can never reach "high"); domain-neutral claim packs (fork = "add a 10-line pack," not "rewrite the app"); derived calls (a transcript lead proposes the next call, human-approved).

## Why CALL-E is essential (not bolted on)

Remove CALL-E and the product ceases to exist — the entire thesis is "retrieve the fact that only lives in a human's head, over the phone." CALL-E is in the business-critical path: `plan_call → run_call → get_call_run` is the verification step itself. Runtime usage is genuine and visible (Stage-One gate + Technical Implementation). We also ship as a reusable **Agent Skill** (`skills/phone-claim-verifier/`) so the contribution outlives our demo.

## Likely competitors (what most teams will build)

- Generic "AI receptionist / AI calls a restaurant to book a table" demos.
- Appointment-scheduling and reminder bots.
- Customer-support callback agents.
- Single-call novelty ("my agent ordered a pizza").

Common pattern: **happy-path, single-call, no evidence discipline, no reusability story, no failure taxonomy.**

## Our differentiation

| Axis | Most entries | Ghostline |
|---|---|---|
| Calls | One, scripted, happy path | Batch, with terminal states for every failure mode |
| Output | "It worked!" | Structured attestation + provenance + `corrections.csv` |
| Honesty | Confident guess | Refuses to guess without a verbatim span; UNCLEAR is a feature |
| Reusability | Bespoke | Domain-neutral engine + 10-line claim packs; ships as a Skill |
| Trust | None | Audit trail, expiry, source-role confidence caps, dial allowlist |
| Innovation beat | — | Derived calls: "the answer wrote the next call" |

## Strongest judge-facing advantages

1. **Real World Impact** (first tiebreaker): federal-statute-backed, $2.76B/year problem, credible buyers.
2. **Evidence discipline** reads as engineering maturity to an AI Rudder domain expert.
3. **Reusability**: one honest answer to "what do I change to fork this?" → "a claim pack."
4. **Honest metrics**: UI reads `benchmark/results.json`, structurally can't display an unmeasured number.

## Biggest weaknesses / highest-risk assumptions

| Weakness | Plan |
|---|---|
| **Time**: ~12 working days, greenfield, **full master-doc scope** (entrant's decision: build everything, minimise nothing) | Risk-first sequencing; CLI vertical slice first to de-risk the spine, then expand to full scope. The master doc §8.1 cut-order exists as a **contingency only** — it is not the plan. Check slip-triggers daily. |
| International call routing to SG judges unproven | Test today (Risk #1) |
| Call budget (20 free + maybe 200) vs benchmark + demo + judging reserve | Code-enforced credit floor + Replay fallback; reserve 80 for judging (master doc §1.7 allocation) |
| Console + deploy is "never cut" and costly | Thin FastAPI + server-rendered HTML over the same engine; deploy early, keep it boring |
| Extraction quality on messy real transcripts | Replay fixtures tune it before live calls; UNCLEAR is an acceptable, honest output |
| Solo builder, no slack for illness/infra fire | 2-day margin before deadline; submit Sep 12 |
| 13 cherries + 2 demoed packs + derived calls on a compressed clock | Cherries are cheap by design (reuse Core data, no new CALL-E surface) and built in the master doc §4.12 order; each is independently demoable and independently cuttable **if** a slip-trigger fires — but the target is all 13 |

## P0 — submission-critical (must ship)

1. Replay harness + 9 fixtures.
2. Claim-pack loader + healthcare pack.
3. CALL-E call engine: `policy_gate → plan_call → run_call → get_call_run`, all terminal states, retries, cancellation.
4. Extractor with evidence-span-or-abstain enforced in code.
5. 4-verdict evaluator + provenance record + expiry calc.
6. `corrections.csv` export (MISMATCH only; UNCLEAR never becomes a correction).
7. Dial allowlist + prompt-injection resistance (transcript can't redirect a call).
8. Web console: CSV upload **and** manual-entry form (same flow), transcript pane, verdict, corrections download.
9. Hosted, health-checked, survives the judging window; session rate-limit + credit floor.
10. `SKILL.md` complete; PR to `awesome-phone-call-agents` passing `validate_repository.py`.
11. Demo video ≤ 3:00.
12. Devpost submission with the 4 criteria as literal headers.
13. `benchmark/results.json` generated from 40–50 real/labelled calls (25 is the contingency floor).
14. ~8 unit tests (§5.10 of master doc).

## P1 — planned, full master-doc scope (entrant: build everything)

- **Derived calls** (single-hop proposal → human approval → policy gate) — the innovation beat.
- **Supplier/CRM claim pack, fully demoed on camera** (proves domain-neutrality live).
- **Community-service pack** as a ~10-line YAML in `examples/` (config-only, per master doc §4.5).
- **Auto-generated claim packs** (§4.12a) — plain-English → draft pack → human approval.
- **All 13 cherries** (master doc §4.12), built cheapest-first in the §4.12 order:
  (j) budget meter → (g) duplicate-number guard → (l) QR code → (h) confidence coloring →
  (a) auto-generated claim pack → (e) audio playback → (b) recheck interval → (d) batch summary →
  (m) trust score → (i) diff view → (c) escalation suggestion → (k) timezone scheduling →
  (f) explain-this-verdict.
- **Reliability benchmark: 40–50 real/labelled calls** (master doc §5.9 / §8 Day 19).

Contingency only (master doc §8.1 cut order, triggered by a slip, never pre-emptively):
cherries in reverse build order → derived-call sophistication → supplier pack on-camera demo →
benchmark size (25 floor).

## Features we are NOT building (kill list — master doc §3, still binding)

Scale claims requiring 1000s of calls · Wilson intervals / statistical sampling frames · public
"Ghost Index" registry · FHIR ingestion · network-adequacy recomputation / duplicate-cluster
detection · 6-state *visible* verdict taxonomy (4 visible, richer tags internal) · **public**
playback of third-party voices · real brand/clinic names or logos · external consented human
panel · 3 fully-demoed packs (2 demoed + 1 config) · giant analytics/BI dashboard · JSON export
alongside CSV · confusion-matrix-as-demo-centerpiece. Post-hackathon tier (write down, don't
build): multi-language auto-detection · public shareable report links · Slack/email MISMATCH
alerting · cross-batch trend analytics · full geo/timezone service beyond an area-code lookup.

## Evidence we need to collect while building

- `benchmark/results.json` (generated): n_calls, human_agreement_rate, abstention_rate, failure_taxonomy.
- 3–4 call transcripts showing MATCH, MISMATCH, UNCLEAR, NO CONTACT.
- The "we take most commercial plans" → UNCLEAR fixture result (the credibility beat).
- Passing unit test output (evidence-span enforcement, dial allowlist, injection resistance).
- One recorded derived-call sequence if P1 ships.
- `FEEDBACK.md` log for the separate Most Valuable Feedback prize.

## Demo strategy

Target 2:35–2:45. Open on the hosted URL with the lifecycle line + "Ghostline can call you — try it yourself." Then: fictional record → real call to a labelled own test line → transcript streams → MISMATCH with highlighted evidence span + expiry → **UNCLEAR beat** (do not cut) → `corrections.csv` opens → derived call if built → pack-swap line → lifecycle diagram → close "it's still online right now, call yourself." Persistent lower-third shows the live benchmark stat. Fictional names only, no trademarks, no unlicensed music/voices.

## Submission strategy

- Draft PR open early (target ~Sep 6), evolving commits, not a deadline-day dump.
- `skills/phone-claim-verifier/` (Agent Skill area) + a stub under `apps/` referencing the hosted console.
- Devpost description: 4 judging criteria as literal `##` headers, in official order; link PR + video + hosted URL.
- Submit **Sep 12**, ~2 days before the 8:45 PM GMT+5 Sep 14 deadline.
- CALL-E Feedback Survey after submission, within the Feedback Period (through Sep 18).
- Aim copy at **Most Practical Use Case ($4,000)**; Most Innovative is upside, don't dilute.
