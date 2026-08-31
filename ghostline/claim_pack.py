"""Claim-pack loading. A claim pack is a YAML file; loading one is the *only* thing you do
to point Ghostline at a new domain.

    pack = load_pack("healthcare")            # by name, from examples/
    pack = load_pack_file(Path("my.yaml"))    # by path

The reusability test (master doc §4.5): "If I fork this tomorrow for supplier records, what
do I change?" -> "Add a claim pack." Not: "rewrite the application."
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .config import REPO_ROOT
from .models import ClaimPack

PACKS_DIR = REPO_ROOT / "examples"


def load_pack_file(path: Path) -> ClaimPack:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path}: claim pack must be a YAML mapping")
    return ClaimPack.model_validate(data)


def load_pack(name: str) -> ClaimPack:
    """Load a bundled pack by id. `name` may be the bare id ('healthcare') or a filename."""
    candidates = [
        PACKS_DIR / name,
        PACKS_DIR / f"{name}.yaml",
        PACKS_DIR / f"{name}.yml",
        PACKS_DIR / f"{name}-pack.yaml",
    ]
    for c in candidates:
        if c.is_file():
            return load_pack_file(c)
    available = sorted(p.stem for p in PACKS_DIR.glob("*.y*ml"))
    raise FileNotFoundError(f"no claim pack {name!r} in {PACKS_DIR} (have: {', '.join(available)})")


def list_packs() -> list[ClaimPack]:
    return [load_pack_file(p) for p in sorted(PACKS_DIR.glob("*.y*ml"))]
