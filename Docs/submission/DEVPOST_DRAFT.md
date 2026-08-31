# Devpost submission — draft

**One-line:** Ghostline is a phone-powered data-verification engine: give it a table of
records and the claims attached to them, and it calls each number via CALL-E, returns
MATCH / MISMATCH / UNCLEAR / NO CONTACT for every claim **with the exact words the person
used** as evidence, and exports a corrections file. It never returns a verdict it can't quote.

**Links:** live app `https://ghostline-one.vercel.app` · repo
`https://github.com/bilalhassan-567/GhostLine` · PR `<awesome-phone-call-agents PR URL>` ·
video `<YouTube/Vimeo URL>` · CALL-E account email `<the one on the CALL-E dashboard>`

**Built during the submission period** (newly created, from scratch).

---

## Real World Impact

Every organisation has a database that is quietly rotting — provider directories, CRM
contacts, supplier records, service listings. The facts that go stale fastest — "is this
office still here", "do they still accept this plan", "is this still the contact" — don't
live in any API. They live in a person's head and decay constantly.

The numbers are not small. CMS's own national review found **48.74%** of Medicare Advantage
provider-directory locations had at least one inaccuracy. A Senate Finance Committee
secret-shopper study found an **18%** appointment-booking success rate. AJMC found **40.3%**
of already-known directory errors persisted an average of **540 days** against a 90-day
federal standard. CAQH puts directory maintenance at **$2.76B/year** for U.S. practices. And
the REAL Health Providers Act (signed Feb 2026) makes *measuring* directory accuracy a
federal statutory obligation for the first time.

Healthcare is the flagship evidence case, not the product's identity. The same problem —
a phone-reachable record that has to stay accurate — is a supplier-contact database, a
211-style community-services directory, any B2B record with a number attached. Ghostline's
engine is domain-neutral; a new domain is a ten-line claim pack.

Who buys it: a health-plan network team, a procurement team, a sales-ops team, a 211
operator — anyone who today pays staff to make these calls by hand, or (worse) doesn't make
them and eats the error rate. What changes Monday: an evidence-backed `corrections.csv`
instead of a guess.

## Quality of the Idea

The non-obvious move is what Ghostline **refuses** to do. Most "AI that calls people" demos
place one happy-path call and report success. Ghostline's core primitive is
**evidence-span-or-abstain**: a MATCH or MISMATCH verdict is *impossible* to produce unless
the extractor identifies a verbatim quoted span from a recipient's turn that supports it. No
span → forced UNCLEAR, stated as intellectual honesty, not an error.

This flips the usual demo. In our recorded scenarios, CALL-E's own extractor reads "we take
most commercial plans" as `accepts_plan = yes` with high confidence. Ghostline abstains —
because no quote named the plan. A skeptical judge can watch the system decline where a
confident model would commit.

Around that sit: an **attestation-not-truth** data model (a timestamped record of what a
specific source said, with a source-role that caps confidence — an answering service can
never reach "high"); **expiry** (every attestation has a re-verification clock); **derived
calls** ("the answer wrote the next call" — a transcript lead becomes a proposed follow-up,
human-approved, re-entering the same safety gate); and **claim packs** — the whole
reusability story is "add a config file", provable live by generating one from a sentence.

## Technical Implementation

CALL-E is used at runtime through two surfaces, deliberately:

- **Python SDK** (`calle-ai`) powers the hosted console and CLI engine. The flow:
  `PolicyGate.plan()` builds a `task` string and a JSON-Schema `result_schema` from the
  claim pack → `client.calls.create(task, recipients=[{phones,region,locale}], result_schema,
  idempotency_key)` → on a persistent host, poll `wait_for_result`; on serverless (Vercel),
  pass a `webhook_url` and resolve at `POST /calle/webhook` → normalize
  `recipients[].attempts[].transcript_turns[]` into our own `Transcript`.
- **MCP** (`plan_call` → `run_call` → `get_call_run`) powers the reusable Agent Skill
  (`skills/phone-claim-verifier/`), where the confirm-token split is the "don't dial until a
  human approves" gate.

Ghostline runs its **own** extraction over the transcript (verbatim span required, and a span
the model invents is dropped in code before it can matter); CALL-E's `structured_result` and
`completion_confidence` are stored only as a secondary signal.

Engineering: a hard `VerdictError` invariant guard, a **dial allowlist** with an explicit
prompt-injection test (a transcript saying "call our other office at +1…" cannot change the
dial target), retries and every terminal-state mapping, an append-only SQLite attestation
ledger, a fixture replay harness that runs the whole pipeline with zero live calls, **60
tests**, `ruff` clean, CI on every push, and a benchmark script whose output the UI reads
from disk — so it is structurally impossible to display a number that wasn't measured.

We also filed detailed CALL-E feedback (see the repo's `Docs/research/CALL_E_FEEDBACK.md`):
no cancel endpoint, undocumented webhook signature headers, one-shot vs. goal result-shape
divergence, and more.

## Product Experience & Demo

One screen. Type a record — or upload a CSV — pick a claim pack, choose Replay (explore 9
recorded calls, no dialing) or Live (Ghostline calls the number you typed). Anyone, including
a judge, tries the real product by typing their own name and number into the same form every
other user uses — there is no separate "demo mode". The result page shows a chat-style
transcript with the evidence span highlighted, the verdict with its provenance and expiry, a
plain-English batch summary, and — when a call surfaces a lead — a one-click derived-call
proposal. `corrections.csv` downloads from the same page.

Safety is visible: a verification only ever calls the number on the record you added or
uploaded, never any other number; dry-run is the default; a hard credit floor falls back to
Replay Mode.

## What's next

Live-call reliability numbers from a labelled batch (the harness is built; it needs real
calls). A published CALL-E Goal for the healthcare pack so `goals.run` is demoed alongside
`calls.create`. Multi-language callee detection. A shareable per-report link. Slack/email
alerting on MISMATCH.
