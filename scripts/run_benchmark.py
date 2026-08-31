#!/usr/bin/env python3
"""Generate benchmark/results.json. Never edit that file by hand.

    python scripts/run_benchmark.py                    # fixture-derived (deterministic, no calls)
    python scripts/run_benchmark.py --source live --csv benchmark/live_records.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ghostline.benchmark import run_live_benchmark, run_replay_benchmark, write_results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["replay", "live"], default="replay")
    ap.add_argument("--csv", type=Path, help="records CSV with a `label` column (live only)")
    args = ap.parse_args()

    if args.source == "live":
        if not args.csv:
            ap.error("--source live needs --csv")
        results = run_live_benchmark(args.csv)
    else:
        results = run_replay_benchmark()

    path = write_results(results)
    print(json.dumps(results, indent=2))
    print(f"\n-> wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
