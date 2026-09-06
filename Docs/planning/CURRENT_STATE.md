# Ghostline — Current State

**Last updated:** 2026-09-06 · **Deadline:** Sep 14, 8:45 PM GMT+5 (submit target Sep 12)

The Aug-31 version of this file described a greenfield repo. That's long gone. This is the
state after the build sprint (Aug 31) and the UI rebuild (Sep 6).

---

## Built and working

| Area | State |
|---|---|
| **Engine** (`ghostline/`) | claim packs (yaml+json), policy gate (dial allowlist + plan/authorize split), call engine (poll + webhook `dispatch`), transcript normalizer, heuristic + LLM extractors, verdict evaluator (evidence-span-or-abstain + `VerdictError` guard), corrections export, SQLite attestation ledger (+ trust score, prior-attestation lookup) |
| **Derived calls** | `ghostline/derived.py` — detects a new contact / a move / another number → proposal card → one-click human approval → re-enters the policy gate. Transcript numbers never auto-dial. |
| **Pack generator** | `ghostline/pack_generator.py` — plain-English sentence → draft pack (LLM or deterministic template) → human-approve page → save. Auto recheck-interval from keywords. |
| **Benchmark** | `ghostline/benchmark.py` + `scripts/run_benchmark.py` → `benchmark/results.json`. Fixture mode (honest "pipeline check" label) + `--source live`. Landing page reads it. |
| **Web console** (`ghostline/console/`) | FastAPI. One screen: manual entry + CSV upload, replay-scenario explorer, `/packs` browser + generator, derived-call approval, `/calle/webhook` receiver, `store_kv` (Upstash-or-memory run store), `/health`. **UI rebuilt Sep 6** — editorial/instrument design, verdict readouts, pulled evidence quotes, document-style transcript, QR "try it" card, healthcare-forward landing. |
| **CLI** | `ghostline packs \| replay \| verify [--live]` |
| **Agent Skill** (`skills/phone-claim-verifier/`) | Standalone stdlib scripts (`plan.py`, `verdict.py`, `_pcv.py`) + `SKILL.md` + 5 references + runnable example. Passes `awesome-phone-call-agents` skill-validation rules (simulated). The submission PR's contribution. |
| **Claim packs** | healthcare (flagship), supplier-crm, community-services — proves domain-neutrality 3 ways, plus generate-from-a-sentence |
| **Cherries** (master doc §4.12) | done: batch summary, duplicate-number guard, QR, confidence-tinted evidence, per-number trust badge, re-verification diff, timezone-ordered queue, escalation hints. (e) audio playback → transcript replay (D-010, no audio API). Budget meter is a placeholder (no live credit tracking). |
| **Tests / CI** | 62 tests, `ruff` clean, `.github/workflows/ci.yml` + `keepwarm.yml` |
| **Deploy** | Vercel — **https://ghostline-one.vercel.app**, live, healthy, Replay Mode |
| **Git** | `github.com/bilalhassan-567/GhostLine`, `main`, ~25 commits, no secrets, no AI attribution |
| **Docs** | README (mermaid architecture), `Docs/demo/DEMO_SCRIPT.md`, `Docs/submission/{DEVPOST_DRAFT, CALL_E_PR_CHECKLIST, SUBMISSION_CHECKLIST, FINAL_GAP_ANALYSIS}.md`, `Docs/research/CALL_E_INTEGRATION.md` + `CALL_E_FEEDBACK.md` |

## Positioning (confirmed 2026-09-06)

The **engine is dynamic** (any phone-reachable record via claim packs + the generator). The
**pitch and demo lead with one industry**: U.S. health-plan provider directories — the CMS
48.74% number, the $2.76B/yr cost, the REAL Health Providers Act. Aim the copy at **Most
Practical Use Case**. The dynamic capability is shown as proof it generalizes, not as the
headline. → [DECISIONS.md](DECISIONS.md) D-020, [COMPETITIVE_STRATEGY.md](COMPETITIVE_STRATEGY.md).

## Not done — all blocked on the entrant

1. **Switch Live mode on** — set Vercel env vars (`CALLE_API_KEY`, `GHOSTLINE_MODE=live`,
   `GHOSTLINE_WEBHOOK_BASE=https://ghostline-one.vercel.app`, `CALLE_WEBHOOK_SECRET`,
   `UPSTASH_REDIS_REST_URL` + `_TOKEN`, `LLM_API_KEY`), redeploy.
2. **Test calls** — own line + international. Confirm routing; capture real voicemail/IVR
   `failure_code` strings for `calle_normalize._FAILURE_TAGS`.
3. **Live benchmark** — `scripts/run_benchmark.py --source live --csv <labelled test lines>`.
4. **Demo video** — script ready in `Docs/demo/`.
5. **Open the PR** — checklist in `Docs/submission/CALL_E_PR_CHECKLIST.md`.
6. **Devpost** — draft ready; fill the form, submit by Sep 12.
7. Enable the two GitHub Actions; submit the CALL-E Feedback Survey by Sep 18.

## Risks now

| Risk | Status |
|---|---|
| Time (8 days, entrant hasn't started the critical path) | Medium. The work is ~1 focused day. Needs to start. |
| International call routing unproven | Untested — Day-1 task never done. `unsupported_region` gives a clean signal if it fails. |
| Benchmark shows only a fixture "pipeline check", not live reliability | Honestly labelled in the UI; real number needs a live batch. |
| `+200` calls request (submitted Aug 31) | Should be processed by now — entrant to confirm on the dashboard. |
