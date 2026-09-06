# Ghostline — go-live playbook

From where the project is now (built, deployed in Replay Mode) to **submitted**. ~1 focused
day of work, split below. Everything external is free and needs no credit card.

---

## The stack (locked)

| Piece | Choice | Why |
|---|---|---|
| Hosting | **Vercel** Hobby | free, no card, already deployed at `ghostline-one.vercel.app` |
| LLM (extractor + pack generator) | **Gemini** free tier, **in a new Google Cloud project** | free, no card; a new project keeps the quota separate from your other app |
| Run store (serverless) | **Upstash Redis** free tier | free, no card; lets the webhook and the browser poll hit different function instances |
| CALL-E | your existing account + the free `+200` request | — |

**One decision:** the webhook signing secret (`CALLE_WEBHOOK_SECRET`) is **optional**. Ship
without it first — the `/calle/webhook` handler parses the unsigned payload, places no calls,
and only updates one run's display. Add signing later if you want the hardening.

---

## Phase A — accounts & keys (~20 min)

### A1. Gemini key
1. https://aistudio.google.com/apikey → **Create API key** → **Create API key in a new project**
   (a new project keeps the free daily quota separate from your other app's).
2. Copy it. Newer keys are prefixed `AQ.` (older ones `AIza`); either works.
3. Ghostline defaults to `GEMINI_MODEL=gemini-3.6-flash` (free tier). If the daily limit looks
   tight at https://aistudio.google.com/rate-limit, set `GEMINI_MODEL=gemini-flash-lite-latest`.

### A2. Upstash Redis
1. https://console.upstash.com → sign up (email, no card).
2. **Create Database**: Name it anything (e.g. `ghostline`); **Primary Region** = pick the one
   closest to Washington D.C. / `us-east-1` (that's where Vercel Hobby runs functions); leave
   **Read Regions** empty and **Eviction** off → **Next** → **Free** plan.
3. On the database page, scroll to the **REST API** block and copy both:
   - `UPSTASH_REDIS_REST_URL` (looks like `https://xxx.upstash.io`)
   - `UPSTASH_REDIS_REST_TOKEN`

### A3. CALL-E
1. Log into https://dashboard.heycall-e.com → **Billing**: note the remaining free-call
   balance. Confirm the `+200` request (submitted Aug 31) has landed; if not, it's
   first-come-first-served — check the Discord / re-submit the form.
2. Keep the API key you already have (`iams_live_…`).

---

## Phase B — switch Vercel to Live (~10 min)

### B1. Add env vars
Vercel → the `ghostline` project → **Settings → Environment Variables**. For each, set
**Production** and **Preview**:

```
GHOSTLINE_MODE            live
GHOSTLINE_WEBHOOK_BASE    https://ghostline-one.vercel.app
GEMINI_API_KEY            AQ.… or AIza…                   (from A1)
UPSTASH_REDIS_REST_URL    https://xxx.upstash.io         (from A2)
UPSTASH_REDIS_REST_TOKEN  …                              (from A2)
```
(`CALLE_API_KEY` is already there. `GEMINI_MODEL` only if you need the Lite model.)

### B2. Redeploy
Vercel → **Deployments** → latest → **⋯ → Redeploy** (or push any commit).

### B3. Verify
```
python scripts/vercel_logs.py env        # every var shows "set", nothing "MISS"
```
Then open `https://ghostline-one.vercel.app/health` → should read `"mode":"live"`,
`"calle_configured":true`, `"llm_configured":true`. On the landing page the **Mode** dropdown
now offers **Live**.

---

## Phase C — prove it works (~30 min + a few calls)

### C1. Call yourself
On the live site: **Add a record** — your name, your phone in E.164, pick the healthcare pack,
set `accepts_plan` to `yes`, Mode = **Live** → **Run verification**. Answer the call. Say
something that contradicts (e.g. *"no, we stopped taking that plan"*) so you get a **MISMATCH**
with your words quoted. Watch the run page resolve.

### C2. Call an international number
Repeat with a non-US number you can answer (or a friend's, with their OK). If it fails with
`unsupported_region` — that's a real finding; tell me and we adjust the messaging. If it
connects, routing is proven.

### C3. Capture failure behaviour
Call a number that rings out / goes to voicemail. On the run page, open the transcript and note
the `status` / `failure_code` shown. **Paste that to me** — I'll finalize the voicemail/IVR
mapping in `calle_normalize.py` (right now it's a best guess).

### C4. Live benchmark
Make a CSV of ~15–40 rows: your test line(s), each with a claim value and a `label` column
holding the verdict you *know* is correct (`MATCH` / `MISMATCH` / `UNCLEAR` / `NO_CONTACT`).
Then:
```
python scripts/run_benchmark.py --source live --csv your_labelled.csv
git add benchmark/results.json && git commit -m "chore: live reliability benchmark" && git push
```
The landing page will switch from "pipeline check" to the real agreement rate.
(Do smaller batches across days if the Gemini quota is tight.)

---

## Phase D — deliverables (~3 hrs)

### D1. Demo video (~1–2 hrs)
Follow `Docs/demo/DEMO_SCRIPT.md` beat by beat. Target 2:35–2:45, hard cap 3:00. Record the
real call from C1. Upload **unlisted** to YouTube/Vimeo first, review, then set **public**.
Nothing on screen may show an API key, token, or a real brand/logo.

### D2. The PR to `awesome-phone-call-agents` (~20 min — I drive it)
1. Fork `https://github.com/CALLE-AI/awesome-phone-call-agents` to your account.
2. Tell me it's forked — I'll run the branch/copy/validate steps from
   `Docs/submission/CALL_E_PR_CHECKLIST.md`.
3. You approve the push and click **Create pull request** on github.com.

### D3. Devpost (~30 min)
1. `call-e.devpost.com` → your submission → paste from `Docs/submission/DEVPOST_DRAFT.md`
   (the 4 criteria are already the section headers).
2. Fields: PR URL (from D2), video URL (from D1), CALL-E account email
   (`mbilalhassan567@gmail.com`), demo URL (`https://ghostline-one.vercel.app`).
3. **Submit** — as *complete*, not draft. Target **Sep 12**, a couple of hours before the
   8:45 PM GMT+5 Sep-14 deadline at the latest.

### D4. Loose ends (~10 min)
- GitHub → your `GhostLine` repo → **Actions** tab → enable workflows (CI + keep-warm).
- After submitting: fill the **CALL-E Feedback Survey** (separate $200 prize, one per person)
  from `Docs/research/CALL_E_FEEDBACK.md` — due **Sep 18**.

---

## Fallback if Phase B is fighting you

If the webhook + Upstash path won't cooperate before the deadline: leave the hosted URL in
**Replay Mode** (it already works for judges) and record the C1 "call yourself" demo from a
**local** run instead — `uvicorn ghostline.console.app:app` on your machine with
`GHOSTLINE_MODE=live` and `GEMINI_API_KEY` in `.env`, no Upstash needed (the threaded poller
works locally). The video carries the live proof; the hosted URL carries the exploration.

---

## What's already done (don't redo)

Engine, web console (responsive UI), CLI, the `phone-claim-verifier` Agent Skill, derived
calls, the pack generator, the Phase-2 webhook code, the benchmark harness, 3 claim packs, 64
tests, CI config, README + all submission docs. Deployed. `CALLE_API_KEY` set on Vercel.
