# Ghostline — Current State Assessment

**Date of assessment:** 2026-08-31
**Assessed by:** Lead engineer
**Source of truth:** [`Docs/masterdocs/GHOSTLINE_MASTER_DOC.md`](../masterdocs/GHOSTLINE_MASTER_DOC.md)

---

## 1. What exists

| Item | Status | Notes |
|---|---|---|
| Master project document | ✅ Complete, high quality | v1.0, 724 lines. Vision, idea, kill-list, architecture, safety, build plan, risk register, demo shot-list, submission checklist all present. Treat as locked spec. |
| Repository | ❌ Not a git repo | `git init` not run. No remote. |
| Python environment | ⚠️ Present but bare | `.venv` with **Python 3.14.5** and only `pip`. No project deps. 3.14 is very new — watch for missing wheels on some libs. |
| PyCharm project scaffolding | ✅ `.idea/` only | No source code, no `pyproject.toml`, no `requirements.txt`. |
| Source code | ❌ None | `core/`, `console/`, `replay/`, `skills/`, `benchmark/` — none exist. |
| Docs structure | ⚠️ Partial | Only `Docs/masterdocs/`. Planning/research/validation/testing/demo/submission folders being created now. |
| CALL-E integration | ❌ Unknown / not started | Account status, API key, free-call balance, `+200` request — all unconfirmed. **Day-1 blocker.** |
| Tests | ❌ None | |
| Deployment | ❌ None | No hosting target chosen. |
| Demo assets | ❌ None | |
| CALL-E PR | ❌ None | |

**Bottom line: this is a greenfield project. Everything except the plan is unbuilt.**

## 2. The single most important finding — the schedule has moved

The master doc was written **2026-08-18** and planned against **27 days**. Today is **2026-08-31**. Against the Sep 14 deadline we now have **~14 calendar days**, and a disciplined submit-with-margin target of **Sep 12 (~12 working days)**.

**~13 days of the original plan are gone with zero code written.** The build plan in §8 of the master doc is no longer executable as written. A compressed plan is in [`ROADMAP.md`](ROADMAP.md).

Deadline note: master prompt says "Sep 14, 11:45 PM SGT"; master doc §1.1 corrected this to **Sep 14, 8:45 PM GMT+5** citing the live schedule page. **Plan against 8:45 PM GMT+5 Sep 14** and re-verify the schedule page in the final week.

## 3. Risks introduced by the compression

| Risk | Impact | Mitigation |
|---|---|---|
| International/SG call routing fails, discovered late | Fatal to demo credibility | Test **today**, before any code |
| CALL-E account/credits not provisioned | Blocks all live work | Confirm today; submit `+200` request today |
| No time for the reliability benchmark | Weakens Technical Implementation score | Shrink to 25 real calls (master doc §8.1 floor) |
| Console + deploy + manual-entry path is "never cut" but expensive | Could eat the whole back half | Build CLI vertical slice first; console is a thin FastAPI+HTML layer over the same engine |
| Python 3.14 dependency gaps | Lost hours | Pin deps early; fall back to 3.12 venv if a wheel is missing |

## 4. What is still strong

- The idea is genuinely differentiated (evidence-span-or-abstain, attestation-not-truth, claim-pack reuse, derived calls, lifecycle framing).
- The master doc already did the hard thinking: research citations, kill-list, safety mapping, judge psychology. We do not need to re-derive strategy — we need to **execute a compressed slice of it**.
- CALL-E usage is architecturally central, not bolted on — passes Stage-One gate trivially and scores well on Technical Implementation if `plan_call → run_call → get_call_run` is genuinely wired.

## 5. Immediate next actions (today)

1. Confirm CALL-E account + API key + free-call balance; submit `+200` request form.
2. One real call to own phone; one to an international/SG number if arrangeable.
3. `git init`, scaffold repo, `pyproject.toml`, pin deps.
4. Build the Replay harness + 9 fixtures (offline, no calls).
5. Lock stack + deployment target (pending user confirmation).
