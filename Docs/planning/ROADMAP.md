# GHOSTLINE — Compressed Roadmap (full master-doc scope)

**Re-anchored:** start = 2026-08-31 · submit target = **Sep 12** · hard deadline = **Sep 14, 8:45 PM GMT+5**
Supersedes the day-by-day plan in master doc §8 (which assumed an Aug 18 start / 27 days). **Scope
is unchanged from the master doc — everything ships. Nothing is minimised.** This roadmap just
compresses the same scope into the days actually remaining.

**Sequencing principle (unchanged):** retire the biggest risk first. Biggest risk = "will a
Singapore judge's phone actually ring in October." Test it Day 1. Build the CLI spine first so
the risky integration is proven before time is spent widening it.

| Day | Date | Work | Kill-gate — must be true to proceed |
|---|---|---|---|
| **1** | Aug 31 | Confirm CALL-E account + key + free-call balance. **Submit `+200` request form.** `calle mcp tools` shows `plan_call`/`run_call`/`get_call_run`. **One real call to own phone. One international/SG call.** `git init`, scaffold repo, `pyproject.toml`, pin deps, `.env.example`. Start `FEEDBACK.md`. | Int'l routing works (or the manual-entry validation/messaging story is revised *today*) |
| **2** | Sep 1 | Replay harness + all 9 fixtures. `core/claim_pack.py` loader + `examples/healthcare-pack.yaml`. `ghostline verify --dry-run` prints planned calls, 0 live. | `--dry-run` clean on a 10-row fixture CSV |
| **3** | Sep 2 | `core/extractor.py` (JSON-schema structured output, **evidence span REQUIRED**). `core/verdict.py` with evidence-span-or-abstain as a hard assertion. Provenance model + `expires_at`. `core/corrections.py` (MISMATCH only). | "we take most commercial plans" fixture → UNCLEAR |
| **4** | Sep 3 | `core/policy_gate.py` (dial allowlist, E.164, business hours, cadence cap, dry-run, credit floor). `core/call_engine.py`: `plan_call → run_call → poll get_call_run`, every terminal state (§5.6), retries + backoff, cancellation. | 3 real calls end-to-end, cleanly logged |
| **5** | Sep 4 | **CLI vertical slice complete end-to-end** ([VERTICAL_SLICE.md](VERTICAL_SLICE.md)). 8 unit tests passing incl. dial-allowlist + transcript-injection resistance. | `ghostline verify --live` on a 1-row CSV → real call → evidence-backed verdict → `corrections.csv`. **Slip-trigger: not green today → invoke §8.1 cut order.** |
| **6** | Sep 5 | Console backend (FastAPI): CSV upload + manual-entry form (same `Record` → same engine), run verification, SSE/poll transcript feed, verdict + corrections download. Batch (>1 record) path. | Engine untouched; console is a thin layer |
| **7** | Sep 6 | Console frontend: one screen — record / live call / resolution. **Open draft PR** to `awesome-phone-call-agents`. Deploy hosted (staging live). | Stranger understands the screen without narration; PR visible; slip-trigger: not deployed → stop features, fix deploy |
| **8** | Sep 7 | Global live-call safety: session/IP rate cap (2–3), credit-floor → Replay fallback, `/health`. Manual-entry path tested by someone else, ideally another country. Auto-generated claim pack (§4.12a) with human-approval gate. | Friend abroad types own number → real call → verdict resolves |
| **9** | Sep 8 | Derived-call feature: lead detection → proposal card → human approve → policy gate with new number. Expiry rendering + re-verification path. `examples/supplier-crm-pack.yaml` + `examples/community-service-pack.yaml`. | One call's answer visibly authors the next task; pack swap = zero core code change |
| **10** | Sep 9 | **Cherries §4.12, all 13, in build order** (j→g→l→h→a→e→b→d→m→i→c→k→f). Each independently demoable, none touching the call engine/policy gate. | Each cherry demoable; slip-trigger: cut in reverse order as time dictates |
| **11** | Sep 10 | **Reliability benchmark: 40–50 real/labelled calls** (own test lines + fixtures where live calls aren't warranted), human-labelled. `scripts/run_benchmark.py` → `benchmark/results.json`. UI reads from file only. | `results.json` exists with real numbers, whatever they are (25 is the contingency floor) |
| **12** | Sep 11 | `SKILL.md` complete (all §9 sections). `python3 scripts/validate_repository.py` green. Correct branch/folder per `git-naming-conventions.md`. `README.md` + architecture diagram. **Record demo video** (fictional data, no trademarks/logos/unreleased voices/music), target 2:35–2:45. | Maintainer could plausibly merge the PR; video ≤ 3:00 |
| **13** | **Sep 12** | Devpost description (4 criteria as literal `##` headers). **Submit on Devpost** — PR URL, public video URL, CALL-E account email, hosted URL. Finalize PR. | Submission shows complete, not draft |
| **14** | Sep 13 | Buffer. Health-check green, credit counter shows judging reserve intact. Watch Discord for late rule changes. | App up, credits intact |
| — | Sep 14 | Deadline 8:45 PM GMT+5. Nothing risky. | — |
| post | →Sep 18 | Submit CALL-E Feedback Survey from `FEEDBACK.md`. | Survey in within Feedback Period |
| post | Sep 30–Oct 13 | **Judging window — app must survive unattended.** Monitor uptime + credit pool daily. Don't tear down infra. | App never returns a dead page |

## Compression pressure — where the days come from vs. the 27-day plan

The 27-day plan had generous single-purpose days (Day 10–12 console, Day 16–17 derived calls,
Day 18.5 cherries, Day 19 benchmark, Day 20–21 PR, Day 22 video, Day 23 Devpost). This roadmap
fuses those: console is 2 days not 3, PR polish + video share Day 12, Devpost + submit share
Day 13. The CLI-spine-first order (Days 2–5) means the console (Days 6–7) is pure UI over a
proven engine, not new logic. Cherries stay a full day because they are genuinely cheap.

## §8.1 cut order — CONTINGENCY ONLY (triggered by a slip, never pre-emptively)

0. Cherries first, reverse of §4.12 build order (last-built = first-cut).
1. Benchmark size: 40 → 25 (floor, not below).
2. Derived-call sophistication: single-hop proposal only, no chaining.
3. Supplier/CRM pack: drop the on-camera demo, keep the written config.

## Never cut, under any pressure

Manual-entry input path · evidence-span-or-abstain · `corrections.csv` · dial allowlist ·
Replay Mode · PR quality · a hosted experience that survives the judging window · honest
`benchmark/results.json`.

## Slip-triggers (check every evening)

- CLI vertical slice not green by **end of Sep 4** → invoke §8.1 from step 0, re-scope.
- Not deployed by **end of Sep 6** → freeze all feature work, fix deploy.
- No `results.json` by **end of Sep 10** → run whatever calls are possible that day; 15 beats 0.
- Behind by >1 full day at any evening check → cut the next cherry batch and re-baseline.
