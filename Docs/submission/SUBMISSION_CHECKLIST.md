# Submission checklist

Deadline: **Sep 14, 2026, 8:45 PM GMT+5** (= 11:45 PM SGT). Submit target: **Sep 12**.

## Required by the Official Rules

- [ ] **PR opened** to `CALLE-AI/awesome-phone-call-agents` in `skills/phone-claim-verifier/`
      — see [CALL_E_PR_CHECKLIST.md](CALL_E_PR_CHECKLIST.md). `validate_repository.py` green.
- [ ] **Demo video** ≤ 3:00, public on YouTube or Vimeo — see [../demo/DEMO_SCRIPT.md](../demo/DEMO_SCRIPT.md).
      No third-party trademarks, no copyrighted music, no unreleased voices.
- [ ] **Devpost form** complete: PR URL, video URL, text description (4 criteria as `##`
      headers — [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md)), CALL-E account email.
- [ ] **Optional but done:** functional demo URL — `https://ghostline-one.vercel.app`.
- [ ] Submitted as **complete**, not draft, at least a few hours before the deadline.

## Product must actually work (judges may test it through Oct 13)

- [ ] `https://ghostline-one.vercel.app/health` → 200.
- [ ] Replay Mode works end-to-end (no creds needed).
- [ ] Live Mode switched on: `GHOSTLINE_MODE=live`, `CALLE_API_KEY`, `GHOSTLINE_WEBHOOK_BASE`,
      `CALLE_WEBHOOK_SECRET`, `UPSTASH_REDIS_REST_URL` + `_TOKEN`, `LLM_API_KEY` set on Vercel.
- [ ] A stranger (ideally another country) types their own number and gets a real call + verdict.
- [ ] The keep-warm GitHub Action is enabled (Actions tab → enable workflows).
- [ ] Reserved CALL-E call budget for the judging window is untouched.

## Repo hygiene

- [ ] No secrets in git history (`.env` gitignored — confirmed).
- [ ] No AI-tool attribution anywhere (source, commits, PR, Devpost, video) — RULES.md §1.
- [ ] `README.md` current: problem, thesis, mechanism, CALL-E usage, architecture diagram,
      quick start, tests, safety, limitations.
- [ ] `benchmark/results.json` regenerated from the latest fixtures (or from `--source live`).
- [ ] All names fictional; `pytest` + `ruff` green; CI passing on `main`.

## Separate prize — Most Valuable Feedback ($200 × 5, per individual)

- [ ] Submit the CALL-E Feedback Survey during the Feedback Period (through **Sep 18** — after
      the submission deadline). Source: [../research/CALL_E_FEEDBACK.md](../research/CALL_E_FEEDBACK.md).

## Post-announcement (if selected, ~Oct 19)

- [ ] Return the winner affidavit / W-8BEN within **10 business days**.
