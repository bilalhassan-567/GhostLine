"""ghostline — command-line entrypoint.

    ghostline packs                       list available claim packs
    ghostline replay [--extractor llm]    run the 9 fixtures through the full pipeline
    ghostline verify FILE.csv --pack P    plan (default) or place (--live) verification calls

Dry-run is the default. Only --live spends a real CALL-E call.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .claim_pack import list_packs, load_pack
from .config import get_settings
from .corrections import write_corrections_csv
from .csv_io import read_records
from .extractor import HeuristicExtractor, LLMExtractor, get_extractor
from .models import CallOutcome, Verdict
from .pipeline import resolve_record
from .policy_gate import GateDecision, PolicyGate

_CHIP = {
    Verdict.MATCH: "[ MATCH ]",
    Verdict.MISMATCH: "[MISMATCH]",
    Verdict.UNCLEAR: "[UNCLEAR ]",
    Verdict.NO_CONTACT: "[NO CALL ]",
}


def _print_attestation(att) -> None:
    print(f"  {_CHIP[att.verdict]} {att.record_id} / {att.claim_id}")
    if att.evidence_span:
        print(f"            evidence: '{att.evidence_span}'  ({att.source_role.value}, {att.confidence.value})")
    if att.diagnostic_tags:
        print(f"            tags: {', '.join(t.value for t in att.diagnostic_tags)}")
    print(f"            {att.evaluation_reason}")
    if att.expires_at:
        print(f"            attested {att.attested_at:%Y-%m-%d} - valid until {att.expires_at:%Y-%m-%d}")


def cmd_packs(_: argparse.Namespace) -> int:
    for p in list_packs():
        print(f"{p.ref:20} {p.display_name}  ({len(p.claims)} claims, expires {p.expires_after_days}d)")
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    from .replay import run_all

    extractor = LLMExtractor() if args.extractor == "llm" else HeuristicExtractor()
    print(f"Replay Mode - 0 live calls - extractor: {extractor.name}\n")
    results = run_all(extractor)
    for r in results:
        mark = "ok  " if r.ok else "FAIL"
        print(f"{mark} {r.fixture.path.stem:22} {r.attestation.verdict.value}")
    passed = sum(r.ok for r in results)
    print(f"\n{passed}/{len(results)} fixtures resolved as expected")
    return 0 if passed == len(results) else 1


def cmd_verify(args: argparse.Namespace) -> int:
    settings = get_settings()
    pack = load_pack(args.pack)
    records = read_records(args.csv)
    gate = PolicyGate(settings)
    live = args.live
    extractor = get_extractor(settings)

    print(f"{len(records)} record(s) - pack {pack.ref} - mode {'LIVE' if live else 'DRY RUN'}\n")

    if not live:
        for rec in records:
            res = gate.authorize(rec, pack, dry_run=True)
            plan = res.plan
            if plan is None:
                print(f"  [SKIP] {rec.record_id}: {'; '.join(res.messages)}")
                continue
            print(f"  [PLAN] {rec.record_id}  would dial {plan.dial_e164}  ({', '.join(plan.claim_ids)})")
            for m in res.messages:
                print(f"         - {m}")
        print("\nNo calls placed. Re-run with --live to dial.")
        return 0

    from .call_engine import CallEngine

    engine = CallEngine(settings)
    all_atts = []
    calls_made = 0
    for rec in records:
        res = gate.authorize(
            rec, pack, credits_remaining=args.credits, calls_this_session=calls_made, dry_run=False
        )
        if res.decision == GateDecision.BLOCK:
            print(f"  [BLOCKED] {rec.record_id}: {'; '.join(res.messages)}")
            continue
        print(f"  dialing {res.plan.dial_e164} for {rec.record_id} ...")
        transcript = engine.place(res.plan)
        calls_made += 1
        if transcript.outcome == CallOutcome.ERROR:
            print(f"  [ERROR] {transcript.failure_code}: {transcript.failure_message}")
            continue
        atts = resolve_record(rec, pack, transcript, extractor)
        all_atts.extend(atts)
        for att in atts:
            _print_attestation(att)

    n = write_corrections_csv(all_atts, args.out)
    print(f"\n{calls_made} call(s) placed - {n} correction row(s) -> {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ghostline", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("packs", help="list claim packs").set_defaults(func=cmd_packs)

    rp = sub.add_parser("replay", help="run the fixture pipeline, 0 live calls")
    rp.add_argument("--extractor", choices=["heuristic", "llm"], default="heuristic")
    rp.set_defaults(func=cmd_replay)

    vp = sub.add_parser("verify", help="verify records from a CSV")
    vp.add_argument("csv", type=Path)
    vp.add_argument("--pack", required=True)
    vp.add_argument("--live", action="store_true", help="place real CALL-E calls")
    vp.add_argument("--credits", type=int, default=None, help="known remaining CALL-E credits")
    vp.add_argument("--out", type=Path, default=Path("corrections.csv"))
    vp.set_defaults(func=cmd_verify)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
