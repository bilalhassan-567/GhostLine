# GHOSTLINE — Task List

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked · `[-]` deferred

Priority key: **P0** submission-critical · **P1** competitive advantage · **P2** quality · **P3** nice-to-have

---

## Day 1 — de-risk (Aug 31)  ·  **owner: entrant** (CALL-E is entrant's account)

Prerequisite chain — do in this exact order:

- [ ] **P0** Register for the hackathon on Devpost ("Join Hackathon"). Note the Devpost username.
- [ ] **P0** Install CALL-E + create account (20 free calls auto). `calle auth login` → `calle auth status`.
  - Acceptance: authenticated; free-call balance known.
- [ ] **P0** **Submit the Additional Calls Request Form immediately** (first-come-first-served, while supplies last; needs CALL-E login done + Devpost username). Draft blurb in [SUBMISSION](../submission/) / provided in chat.
  - Acceptance: form submitted; email copy received.
- [ ] **P0** Place 1 real call to entrant's own phone. Log transcript + call id.
- [ ] **P0** Place 1 call to an international / Singapore-region number (master doc §4.8 — non-negotiable Day-1 check).
  - Acceptance: routing confirmed, or documented as a Day-1 finding → adjust manual-entry validation/messaging.

Verification tasks (feed doc reconciliation — see [HACKATHON_ANALYSIS.md](../research/HACKATHON_ANALYSIS.md) §3–4):

- [ ] **P0** Read `docs.heycall-e.com/quickstart` + `#/sdks` + `#api-reference` + Build Session (youtu.be/qzHIFuZkCik). Record the **actual** Python SDK / MCP method names + call lifecycle ("goals" model) in `Docs/research/CALL_E_INTEGRATION.md`. Reconcile master doc §4.6 / §5.
- [ ] **P0** Read `awesome-phone-call-agents` README + `docs/git-naming-conventions.md` + `scripts/validate_repository.py`. Confirm exact Contribution Area folder, frontmatter, branch-name rules. Record in `CALL_E_INTEGRATION.md`.
- [ ] **P2** Create `FEEDBACK.md`; log first friction points.

Repo scaffolding (blocked on entrant's git go-ahead — currently on hold):

- [!] **P0** `git init`; `.gitignore` — BLOCKED: entrant holding git. `.gitignore` file written, ready.
- [x] **P0** Scaffold repo (no git): `pyproject.toml`, deps installed in `.venv`, `ghostline/` package, `examples/`, `replay/`, `tests/`, `README.md`, `.env` + `.env.example`.
- [x] **P0** Stack decided: Python/FastAPI (D-001..D-012). Hosting: deferred (O-003).

## Day 2 — offline engine foundation (Sep 1) — **done early, 2026-08-31**

- [x] **P0** `ghostline/claim_pack.py`: domain-neutral YAML loader. `examples/healthcare-pack.yaml` (3 claims).
  - ✅ new pack = new file, zero code change — `tests/test_claim_pack.py`.
- [x] **P0** `replay/fixtures/` — all 9 (MATCH, MISMATCH, UNCLEAR×3 [generic/ambiguous/contradictory], VOICEMAIL, IVR, NO_ANSWER, CALL_FAILED) + `ghostline/replay.py` harness with `_meta` self-check.
- [x] **P0** `ghostline verify <csv> --pack healthcare` dry-run prints planned calls, 0 live. `ghostline replay` runs the pipeline over all 9, 9/9 pass.
- [x] **P0** `ghostline/calle_normalize.py` — shared CallTask→Transcript normalizer (used by replay AND call engine).

## Day 3 — verification layer (Sep 2) — **done early, 2026-08-31**

- [x] **P0** `ghostline/extractor.py`: `HeuristicExtractor` (deterministic, no key) + `LLMExtractor` (anthropic structured; span re-validated verbatim in code, invented spans dropped).
- [x] **P0** `ghostline/verdict.py`: 4-verdict evaluator; hard rule (no verbatim span ⇒ UNCLEAR) + `_assert_invariant` bug-guard.
- [x] **P0** `Attestation` model + provenance fields + `expires_at` (per-pack window) + CALL-E secondary signal fields.
- [x] **P0** `ghostline/corrections.py`: `corrections.csv`, MISMATCH-only. ✅ "we take most commercial plans" ⇒ UNCLEAR (fixture 03).

## Day 4 — call path (Sep 3) — **partially done early**

- [x] **P0** `ghostline/policy_gate.py`: E.164 (`phonenumbers`), per-record dial allowlist, business hours, cadence cap, dry-run, credit floor, session cap, `plan()`/`authorize()` split.
- [x] **P0** `ghostline/call_engine.py`: `client.calls.create → wait_for_result → normalize`; APIError → NO_CONTACT/ERROR mapping; timeout → abandon (no cancel API).
- [ ] **P0** 3 real calls end-to-end, logged — **entrant, tomorrow** (needs live CALL-E account). Capture real voicemail/IVR `failure_code` strings → finalize `calle_normalize._FAILURE_TAGS`.

## Day 5 — vertical slice + tests (Sep 4) — **KILL-GATE — mostly green early**

- [x] **P0** `ghostline/cli.py` wires the full slice: `packs` / `replay` / `verify [--live]`.
- [x] **P0** 31 tests passing (target was 8): evidence-span enforcement (4), dial-allowlist + transcript-injection resistance (3), expiry, corrections-excludes-UNCLEAR, claim-pack loader, 9-fixture correctness, rate/credit/cadence caps. `ruff` clean.
- [ ] **P0** `--live` on own test line → real attestation with real `call_id` — **entrant, tomorrow**.
- **Gate status:** offline slice GREEN. Only the live-call confirmation remains, and it's not on the critical path for anything else.

## Day 6 — console backend (Sep 5) — **done early, 2026-08-31**

- [x] **P0** FastAPI (`ghostline/console/app.py`): CSV upload + manual-entry form (same `Record` → same engine), replay-scenario explorer, live run on a background thread, `GET /api/run/{id}` polling, `corrections.csv` download, `GET /health`.
- [x] **P0** `ghostline/store.py` — append-only SQLite attestation ledger (audit trail; backs trust-score / diff cherries).
- [x] **P0** 6 console tests; **37 tests total**, ruff clean.

## Day 7 — console frontend + PR + deploy (Sep 6) — **frontend done early**

- [x] **P0** One-screen UI (`base+index+run.html`): record / transcript / verdict / evidence span highlighted in the transcript / corrections download. Poll-refresh while a live run is in flight.
- [x] **P0** **Agent Skill built** — `skills/phone-claim-verifier/` (SKILL.md + 5 references + `plan.py`/`verdict.py`/`_pcv.py` stdlib scripts + runnable example). 11 skill tests (**50 total**). Passes the `awesome-phone-call-agents` skill-validation rules (simulated locally). MCP path (`plan_call`→`run_call`→`get_call_run`).
- [~] **P0** Deploy hosted — **Vercel, Replay Mode LIVE** at https://ghostline-one.vercel.app (D-017). Phase 2 (webhook + Upstash → live "call yourself") pending.
- [ ] **P0** Open **draft PR** to `CALLE-AI/awesome-phone-call-agents` — Skill is ready; needs: fork the repo, add `skills/phone-claim-verifier/` + a README resource-list line, `python3 scripts/validate_repository.py`, branch `feat/phone-claim-verifier`, push, open PR. Walk the entrant through it.

## Day 8 — global live-call safety + auto-packs (Sep 7) — **done early**

- [x] **P0** Session live-call cap, credit-floor ⇒ Replay fallback, `/health` (in `policy_gate.py` + console).
- [ ] **P0** Manual-entry path tested end-to-end by someone who is not the entrant — **needs entrant** (test calls first).
- [x] **P1** `ghostline/pack_generator.py` (§4.12a): plain-English → draft pack (LLM or deterministic template) → human-approve page → save/download. Auto `expires_after` from keywords (§4.12b).

## Day 9 — innovation beat + reusability (Sep 8) — **done early**

- [x] **P1** Derived calls (`ghostline/derived.py`): lead detection (contact / move / number) → proposal card → human approve → `start_derived_run` re-enters the policy gate. Transcript numbers never auto-dial.
- [x] **P1** Expiry rendering (`attested … · valid until …`) in the console.
- [x] **P1** `ghostline/data/packs/supplier-crm.yaml` + `examples/suppliers-sample.csv`.
- [x] **P2** `ghostline/data/packs/community-services.yaml` (config-only, incl. an enum claim).

## Day 10 — cherries (Sep 9) — **done early (7 of 13)**

- [x] **P1** (j) mode indicator in the topbar (budget meter is placeholder until live credit tracking)
- [x] **P1** (g) duplicate-number guard — `runs.duplicate_number_groups`
- [x] **P1** (l) "try it yourself" QR code (server-rendered SVG via `segno`)
- [x] **P1** (h) confidence-tinted evidence span (`.evidence.c-high/medium/low`)
- [x] **P1** (a) auto-generated claim pack — see Day 8
- [-] **P1** (e) audio playback → D-010: confidence-colored transcript replay (no audio API); transcript view done
- [x] **P1** (b) auto-suggested recheck interval — in the generator
- [x] **P1** (d) plain-English batch summary — `runs._batch_summary`
- [x] **P1** (m) per-number trust score — `store.trust_score` → badge in the record header
- [ ] **P1** (i) re-verification diff view — `store.prior_attestation()` exists; needs the two-column render
- [ ] **P1** (c) auto-escalation suggestion on low-trust sources — wire to the derived-call button
- [ ] **P1** (k) timezone-aware call scheduling — `_local_hour` exists; needs queue sort
- [x] **P1** (f) "explain this verdict" — `evaluation_reason` shown inline

## Day 11 — reliability benchmark (Sep 10) — **harness done; real numbers need entrant**

- [x] **P0** `ghostline/benchmark.py` + `scripts/run_benchmark.py` → `benchmark/results.json`. Fixture mode (deterministic pipeline check) + `--source live` mode (real calls vs a `label` column). Landing page reads the file; honest labelling ("pipeline check — not a live-call reliability number yet").
- [ ] **P0** Run `--source live` against 25–50 real/labelled calls — **needs entrant + credits**.

## Day 12 — PR polish + demo (Sep 11)

- [x] **P0** `SKILL.md` complete; passes skill-validation rules (simulated).
- [ ] **P0** `python3 scripts/validate_repository.py` green in the fork — **needs the fork + PR walkthrough**.
- [x] **P0** `README.md` — problem/thesis/mechanism/quick-start/CALL-E/mermaid architecture/skill/extending/tests/safety/deploy/limitations.
- [ ] **P0** Record video ≤ 3:00 (target 2:35–2:45). Fictional data only. Shot list = master doc §10.2 (incl. UNCLEAR beat, derived-call beat, auto-pack + audio beat, pack-swap beat).

## Day 13 — SUBMIT (Sep 12)

- [ ] **P0** Devpost description — 4 judging criteria as literal `##` headers.
- [ ] **P0** Devpost submission complete: PR URL, public video URL, CALL-E account email, hosted URL.
- [ ] **P0** Finalize PR (entrant pushes).

## Day 14 + judging window

- [ ] **P0** Buffer / monitoring. Health-check green, judging credit reserve intact.
- [ ] **P1** CALL-E Feedback Survey from `FEEDBACK.md` (by Sep 18).
- [ ] **P0** Keep infra up Sep 30–Oct 13; monitor daily.

## Deferred (post-hackathon — master doc kill list §3, not scope for this build)

- [-] STALE/EXPIRING/VERIFIED 3-tier status system (one visible expiry date is enough)
- [-] Public "Ghost Index" registry · FHIR ingestion · Wilson intervals / sampling frames
- [-] Giant analytics/BI dashboard · JSON export alongside CSV
- [-] Multi-language auto-detection · public shareable report links · Slack/email MISMATCH alerting
- [-] Cross-batch trend analytics · full geo/timezone service beyond area-code lookup
- [-] Chaining multiple derived calls (single-hop only for the hackathon)
