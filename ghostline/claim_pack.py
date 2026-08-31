"""Claim-pack loading. A claim pack is a YAML file; loading one is the *only* thing you do
to point Ghostline at a new domain.

    pack = load_pack("healthcare")            # by id
    pack = load_pack_file(Path("my.yaml"))    # by path

Packs are searched in two places: `ghostline/data/packs/` (bundled — always available, even
when installed as a wheel or on a serverless host) and a repo-root `packs/` or `examples/`
dir if present (where a developer drops new packs; these take precedence).

The reusability test (master doc §4.5): "If I fork this tomorrow for supplier records, what
do I change?" -> "Add a claim pack." Not: "rewrite the application."
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .config import REPO_ROOT
from .models import ClaimPack

_BUNDLED_PACKS = Path(__file__).parent / "data" / "packs"
# Dev override dirs first, bundled last.
PACK_DIRS = [
    d
    for d in (REPO_ROOT / "packs", REPO_ROOT / "examples", _BUNDLED_PACKS)
    if d.is_dir()
]
PACKS_DIR = PACK_DIRS[0] if PACK_DIRS else _BUNDLED_PACKS  # kept for back-compat


def load_pack_file(path: Path) -> ClaimPack:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path}: claim pack must be a YAML mapping")
    return ClaimPack.model_validate(data)


_PATTERNS = ("*.yaml", "*.yml", "*.json")


def _pack_files() -> list[Path]:
    seen: dict[str, Path] = {}
    for d in PACK_DIRS:
        for pat in _PATTERNS:
            for p in sorted(d.glob(pat)):
                seen.setdefault(p.stem.removesuffix("-pack"), p)
    return list(seen.values())


def load_pack(name: str) -> ClaimPack:
    stem = name.removesuffix(".yaml").removesuffix(".yml").removesuffix(".json").removesuffix("-pack")
    for d in PACK_DIRS:
        for cand in (
            d / f"{stem}.yaml", d / f"{stem}.yml", d / f"{stem}.json",
            d / f"{stem}-pack.yaml", d / name,
        ):
            if cand.is_file():
                return load_pack_file(cand)
    have = ", ".join(sorted(p.stem for p in _pack_files())) or "(none)"
    raise FileNotFoundError(f"no claim pack {name!r} in {[str(d) for d in PACK_DIRS]} (have: {have})")


def list_packs() -> list[ClaimPack]:
    return [load_pack_file(p) for p in _pack_files()]
