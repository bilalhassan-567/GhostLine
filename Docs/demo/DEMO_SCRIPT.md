# Ghostline — demo video script

**Target: 2:35–2:45.** Hard cap 3:00 (judges aren't required to watch past it). Public on
YouTube/Vimeo. Fictional data only, no real brands/logos, no copyrighted music, no unreleased
voices (calls go to the entrant's own labelled test line, or the viewer's own number).

Screen-record at 1080p+. A quiet room. One take per shot, cut together.

---

## Shot list

| Time | On screen | Voiceover (write your own; this is the beat) |
|---|---|---|
| **0:00–0:12** | Landing page at `ghostline-one.vercel.app`. The lifecycle line is visible: *asserted → verified → evidenced → corrected → expired → re-verified*. Cursor hovers the QR block. | "Every company has a database that's quietly rotting — provider directories, supplier contacts, service listings. The facts that go stale don't live in any API. They live in someone's head. Ghostline calls to check." |
| **0:12–0:22** | Type into the form: name `Northline Family Clinic`, a phone number **you control**, `accepts_plan = yes`. Mode: **Live**. Click Verify. | "You give it a record and the claim attached to it. It calls the number — live." |
| **0:22–1:00** | The run page. Status `dialing` → the call connects (you answer your own test line, on speaker or as a second track). Play a short exchange: bot asks about the plan, you say *"No — we actually stopped taking that plan last month."* Status resolves. | "Ghostline places the call through CALL-E, asks the questions, and listens." |
| **1:00–1:20** | The verdict card renders: **MISMATCH** chip. The evidence block shows the exact quote *"we stopped taking that plan last month"* with `front_desk · medium confidence`. Expiry line: *valid until [date]*. | "It doesn't say the office is wrong. It says: this person, at this time, said this — here are their words. And it stamps an expiry, because the answer will go stale too." |
| **1:20–1:40** | Click a **Replay** scenario: `we take most commercial plans`. Verdict: **UNCLEAR**. The contrast line: *CALL-E's own extractor read this as "yes" (high confidence). Ghostline abstained — no verbatim quote named the plan.* | "This is the rule that matters. No verbatim quote, no verdict. A confident model would have said yes. Ghostline won't guess." |
| **1:40–1:55** | `corrections.csv` downloads and opens in a spreadsheet. One row: `accepts_plan, true → false`, with the quote in a column. | "Every mismatch becomes a row someone can act on Monday morning. Unclear answers never do." |
| **1:55–2:12** | Back on the MISMATCH run — the derived-call card: *"The answer wrote the next call. A different contact was named (Sarah). Re-verify asking for Sarah."* Click **Approve**. A new run starts. | "And when a call surfaces a lead — a new contact, a move — Ghostline proposes the next verification. You approve it. The transcript never dials anyone on its own." |
| **2:12–2:25** | The `/packs` page. Type *"verify these restaurants are still open and still take reservations"*. A draft pack appears with two claims. | "A new domain is a new claim pack — ten lines of config, or a sentence. The engine never changes." |
| **2:25–2:38** | Quick cut: the mermaid architecture diagram from the README, then the `skills/phone-claim-verifier/` folder in the repo. | "The engine ships as a reusable CALL-E Agent Skill, and the whole thing runs on a free tier." |
| **2:38–2:45** | Back to the landing page, lifecycle line. | "Ghostline doesn't maintain your database. It tells you when reality has moved on — and it's online right now. Call yourself." |

---

## Prep checklist

- [ ] `GHOSTLINE_MODE=live`, `CALLE_API_KEY`, `GHOSTLINE_WEBHOOK_BASE`, `CALLE_WEBHOOK_SECRET`,
      Upstash creds set on Vercel; redeploy; confirm the form offers **Live**.
- [ ] A test line you control, added to your table, answered on a track you can record.
- [ ] Rehearse the answer: say the mismatch line *and* the "talk to Sarah" line so the
      derived-call card appears.
- [ ] `benchmark/results.json` regenerated so the landing strip is current.
- [ ] Nothing on screen shows an API key, token, `plan_id`, or `confirm_token`.
- [ ] Record the "we take most commercial plans" beat from **Replay** (deterministic, no call spent).
- [ ] Final length ≤ 3:00. Upload unlisted first, review, then set public.
