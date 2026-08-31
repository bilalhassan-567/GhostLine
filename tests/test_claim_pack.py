"""A new domain is a new file — not a code change."""

from pathlib import Path

from ghostline.claim_pack import list_packs, load_pack_file
from ghostline.models import ClaimPack


def test_healthcare_pack_loads(healthcare):
    assert healthcare.pack_id == "healthcare"
    assert healthcare.ref == "healthcare@1"
    assert {c.claim_id for c in healthcare.claims} == {
        "accepts_plan", "accepting_new_patients", "address_current"
    }
    assert healthcare.expires_after_days == 90


def test_brand_new_pack_from_a_file_needs_zero_code(tmp_path: Path):
    yaml_text = """
pack_id: locksmiths
version: 1
display_name: Emergency locksmith directory
expires_after_days: 30
claims:
  - claim_id: open_24h
    question: Are you open 24 hours for emergency callouts?
    expected_type: boolean
    subject_terms: ["24 hour", "24/7", "emergency", "callout"]
"""
    p = tmp_path / "locksmiths.yaml"
    p.write_text(yaml_text, encoding="utf-8")
    pack = load_pack_file(p)
    assert isinstance(pack, ClaimPack)
    assert pack.claim("open_24h").expected_type.value == "boolean"


def test_examples_dir_packs_all_valid():
    packs = list_packs()
    assert any(p.pack_id == "healthcare" for p in packs)
    for p in packs:
        assert p.claims, f"{p.pack_id} has no claims"
