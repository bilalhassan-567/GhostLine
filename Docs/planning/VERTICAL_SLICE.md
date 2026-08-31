# GHOSTLINE — Smallest P0 Vertical Slice

**Goal:** the minimum end-to-end path that proves the *entire* concept is real — CALL-E at
runtime, evidence-span-or-abstain, provenance, corrections output, the lifecycle. Everything
else (console, manual entry, derived calls, cherries, second claim pack) is expansion on top
of this spine.

## The slice

```
ghostline verify examples/one_provider.csv --pack healthcare --live
```

1. Load a **1-row CSV** (`record_id, name, phone, address, accepts_plan`).
2. Load the **healthcare claim pack** (YAML) → generate the call goal text from the claim.
3. **Policy gate**: validate the phone as E.164, confirm it is on the per-record allowlist
   (i.e. it *is* the number on the row), check dry-run flag, check credit floor.
4. **CALL-E**: `plan_call` → `confirm_token` → `run_call` → poll `get_call_run` until a
   terminal state. Handle no-answer / voicemail / IVR / failure → `NO_CONTACT` path.
5. **Extractor** (LLM, strict JSON schema): pull `answer_text` + a **required** verbatim
   `evidence_span`. No span → `None`.
6. **Verdict evaluator**: hard assertion — no evidence span ⇒ `UNCLEAR`. Otherwise
   `MATCH` / `MISMATCH` from the span vs. the claim.
7. Write the **attestation** with full provenance (`record_id, claim_id, call_id,
   source_role, evidence_span, attested_at, expires_at, verdict, evaluation_reason`).
8. If `MISMATCH`: append a row to **`corrections.csv`**.
9. Print a human-readable summary to stdout.

## What it deliberately excludes (added in later days)

- Web console / manual-entry form (Day 6–7)
- Batch of >1 record, timezone sorting, duplicate-number guard (Day 6+, cherries)
- Derived calls (Day 9, P1)
- Second claim pack (Day 9)
- Benchmark harness (Day 10)
- All cherries

## Definition of done for the slice (Day-5 kill-gate)

- [ ] Runs against **replay fixtures** with `--replay` (no live call) for all 9 fixtures,
      producing the correct verdict for each.
- [ ] Runs **`--live`** against the entrant's own test line and produces a real attestation
      with a real `call_id` from CALL-E.
- [ ] `--dry-run` (default) places 0 calls and prints the planned call.
- [ ] The "we take most commercial plans" fixture returns `UNCLEAR` (no span naming the plan).
- [ ] A fixture whose transcript says "call our other office at 555-…" does **not** change
      the dial target (injection test passes).
- [ ] `corrections.csv` contains only the `MISMATCH` row, never the `UNCLEAR` one.
- [ ] 8 unit tests pass (evidence-span enforcement, dial allowlist, expiry calc, corrections
      excludes UNCLEAR, rate-limit cap, claim-pack loader, verdict-from-fixture ×9,
      injection resistance).

## Build order within the slice

`claim_pack.py` → replay fixtures + `replay/` harness → `extractor.py` → `verdict.py` →
`corrections.py` → `policy_gate.py` → `call_engine.py` → `cli.py` wiring → tests.

Everything from `extractor.py` onward is developed and tested against replay fixtures first;
`call_engine.py` is the last piece and the only one that spends live calls.
