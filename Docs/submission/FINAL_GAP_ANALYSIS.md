# Final gap analysis

As of 2026-08-31 (autonomous build session). Brutally honest.

| Area | Status | Evidence | Missing | Priority |
|---|---|---|---|---|
| Real-world problem | Strong | CMS 48.74%, Senate 18%, CAQH $2.76B, REAL Health Providers Act; domain-neutral framing | Nothing | — |
| Story / stakeholder | Good | README + Devpost lead with the rotting-database problem, not architecture | A sharper 10-second hook in the video | P1 |
| Thesis | Strong | "records what a source said, not truth" + evidence-span-or-abstain; one line, quotable | Nothing | — |
| Core mechanism | Strong | `verdict.py` hard rule + `VerdictError` guard + injection test; the CALL-E-vs-Ghostline contrast beat | Nothing | — |
| CALL-E integration | Strong | SDK (`calls.create` + webhook path) at runtime in the app; MCP in the Skill; verified vs OpenAPI 0.6.0 | Live-call round trip not yet exercised by the entrant | **P0 (entrant)** |
| Technical depth | Strong | 60 tests, CI, replay harness, ledger, allowlist, retries, terminal-state mapping, benchmark-from-file | — | — |
| Ablation / evidence | Partial | `benchmark.py` runs; `results.json` is fixture-derived (pipeline check), honestly labelled | Real numbers from `--source live` against 25–50 labelled calls | **P0 (entrant + credits)** |
| Metrics | Partial | Failure taxonomy + abstention rate generated | Live agreement rate | P0 (entrant) |
| Reliability / failure handling | Strong | every terminal state mapped; NO_CONTACT path; credit floor → Replay fallback; no-cancel documented | Exact voicemail/IVR `failure_code` strings (from real calls) | P1 (entrant) |
| Security | Strong | dial allowlist + injection test; no transcript/LLM number reaches the dialer; XSS-safe transcript render; disclosure in every goal | `security-review` skill pass before submission | P1 |
| Tests | Strong | 60, ruff clean, CI on push | — | — |
| Deployment | Good | Vercel live (Replay); Phase-2 webhook path built, needs env vars | Flip on Live on Vercel (Upstash + CALL-E env) | **P0 (entrant)** |
| Demo | Not started | Script written ([../demo/DEMO_SCRIPT.md](../demo/DEMO_SCRIPT.md)) | Record it — needs Live mode on | **P0 (entrant)** |
| README | Strong | full rewrite w/ mermaid diagram | — | — |
| CALL-E PR | Not opened | Skill built + passes validation (simulated); checklist written | Fork → branch → validate → PR | **P0 (entrant + walkthrough)** |
| Devpost | Draft ready | [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md) | Paste in the form + URLs | **P0 (entrant)** |
| Differentiation | Strong | abstention beat, attestation model, derived calls, reusable Skill, honest metrics | — | — |
| Reusability | Strong | 3 packs + generate-from-a-sentence; Skill is standalone stdlib | — | — |
| MVF feedback | Ready | [../research/CALL_E_FEEDBACK.md](../research/CALL_E_FEEDBACK.md), ~10 concrete items | Submit the survey (by Sep 18) | P1 (entrant) |

## If I were a skeptical judge, what would stop me ranking this highly?

1. **"The benchmark says 100% but it's fixtures."** — Fair. The number on the landing page is
   now framed as "9/9 recorded scenarios resolved correctly — pipeline check, not a live-call
   reliability number." The real number needs a labelled live batch. **Fix: entrant runs
   `--source live` against their test lines.** Until then, don't claim a reliability rate in
   the video — claim the discipline (evidence-span-or-abstain) and show it working.

2. **"Did CALL-E actually run, or is this all replay?"** — The video must show a real call
   placed and resolved on the hosted URL. **Fix: entrant switches Live on and records it.**

3. **"Is the Skill real or a stub?"** — It's real: `plan.py` + `verdict.py` run on stdlib
   alone, 11 tests, passes their validator. The PR makes this checkable. **Fix: open the PR.**

4. **"One-prize rule — is this Practical or Innovative?"** — Aim the copy at **Most Practical**
   (a boring, deployable, ROI-clear workflow). The derived-call / abstention framing is
   Innovative upside; don't split the pitch.

5. **Polish nits:** the budget meter is a placeholder (no live credit tracking); the diff view
   only triggers on a real re-verification (correct, but not demoable via identical replays);
   `(e)` audio playback is swapped for transcript replay (no audio API — documented).

## Highest-impact next actions (entrant)

1. Set the Vercel env vars, redeploy, confirm Live mode, place one real call.
2. Record the demo video.
3. Run `scripts/run_benchmark.py --source live --csv <labelled test lines>`.
4. Open the PR (walkthrough in [CALL_E_PR_CHECKLIST.md](CALL_E_PR_CHECKLIST.md)).
5. Fill the Devpost form from [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md); submit Sep 12.
