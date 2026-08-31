"""Replay harness — run the full pipeline against fixture transcripts, zero live calls.

Build this before the live call engine (master doc §5.7). Every fixture in replay/fixtures/
carries a `_meta` block with the expected verdict, so `run_all()` doubles as a correctness
check on the extractor + verdict evaluator.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .calle_normalize import transcript_from_calltask
from .claim_pack import load_pack
from .config import REPO_ROOT
from .extractor import Extractor, get_extractor
from .models import Attestation, Record, Transcript
from .pipeline import resolve_claim

FIXTURES_DIR = REPO_ROOT / "replay" / "fixtures"


@dataclass
class Fixture:
    path: Path
    meta: dict
    calltask: dict

    @property
    def scenario(self) -> str:
        return self.meta.get("scenario", self.path.stem)

    @property
    def record(self) -> Record:
        return Record.model_validate(self.meta["record"])

    def transcript(self) -> Transcript:
        return transcript_from_calltask(self.calltask)


@dataclass
class ReplayResult:
    fixture: Fixture
    attestation: Attestation
    ok: bool
    detail: str


def load_fixtures() -> list[Fixture]:
    out: list[Fixture] = []
    for p in sorted(FIXTURES_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        meta = data.pop("_meta", {})
        out.append(Fixture(path=p, meta=meta, calltask=data))
    return out


def run_fixture(fx: Fixture, extractor: Extractor | None = None) -> ReplayResult:
    extractor = extractor or get_extractor()
    pack = load_pack(fx.meta["pack"])
    claim = pack.claim(fx.meta["claim_id"])
    att = resolve_claim(fx.record, claim, pack, fx.transcript(), extractor)

    want = fx.meta.get("expected_verdict")
    got = att.verdict.value
    verdict_ok = want is None or got == want

    want_tags = set(fx.meta.get("expected_tags", []))
    got_tags = {t.value for t in att.diagnostic_tags}
    tags_ok = not want_tags or want_tags.issubset(got_tags)

    ok = verdict_ok and tags_ok
    detail = f"verdict {got} (want {want}); tags {sorted(got_tags)} (want {sorted(want_tags)})"
    return ReplayResult(fixture=fx, attestation=att, ok=ok, detail=detail)


def run_all(extractor: Extractor | None = None) -> list[ReplayResult]:
    extractor = extractor or get_extractor()
    return [run_fixture(fx, extractor) for fx in load_fixtures()]
