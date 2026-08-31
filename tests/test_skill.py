"""The phone-claim-verifier skill (skills/phone-claim-verifier/) — standalone stdlib logic."""

import importlib.util
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent / "skills" / "phone-claim-verifier"
PACK = SKILL / "examples" / "healthcare.json"


def _load():
    spec = importlib.util.spec_from_file_location("_pcv", SKILL / "scripts" / "_pcv.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_pcv"] = mod
    spec.loader.exec_module(mod)
    return mod


pcv = _load()
REC = {"record_id": "p1", "name": "Northline Family Clinic", "phone": "+12025550110",
       "claims": {"accepts_plan": True}}
PACK_OBJ = pcv.load_pack(PACK)


def _tr(*users):
    turns = [{"speaker": "bot", "text": "Do you accept the Northline Health plan?"}]
    turns += [{"speaker": "user", "text": u} for u in users]
    return turns


def test_verbatim_span_resolves_mismatch():
    att = pcv.evaluate(
        REC, PACK_OBJ, "accepts_plan",
        {"answer": "no", "evidence_span": "we dropped Northline Health in March"},
        _tr("Sorry, we dropped Northline Health in March."),
    )
    assert att["verdict"] == "MISMATCH"
    assert pcv.corrections_row(att)["evidence"] == "we dropped Northline Health in March"


def test_non_verbatim_span_forced_to_unclear():
    att = pcv.evaluate(
        REC, PACK_OBJ, "accepts_plan",
        {"answer": "no", "evidence_span": "they said they do not take it"},
        _tr("Sorry, we dropped Northline Health in March."),
    )
    assert att["verdict"] == "UNCLEAR"
    assert att["evidence_span"] is None
    assert pcv.corrections_row(att) is None


def test_generic_plans_answer_is_unclear():
    att = pcv.evaluate(
        REC, PACK_OBJ, "accepts_plan",
        {"answer": "unknown", "evidence_span": None},
        _tr("We take most major commercial plans."),
    )
    assert att["verdict"] == "UNCLEAR"


def test_no_recipient_turns_is_no_contact():
    att = pcv.evaluate(REC, PACK_OBJ, "accepts_plan", {"answer": "yes", "evidence_span": "x"}, [])
    assert att["verdict"] == "NO_CONTACT"


def test_match_when_answer_agrees_with_assertion():
    att = pcv.evaluate(
        REC, PACK_OBJ, "accepts_plan",
        {"answer": "yes", "evidence_span": "we take Northline Health"},
        _tr("Yes, we take Northline Health."),
    )
    assert att["verdict"] == "MATCH"


def test_conflicting_flag_forces_unclear():
    att = pcv.evaluate(
        REC, PACK_OBJ, "accepts_plan",
        {"answer": "yes", "evidence_span": "we take Northline Health", "conflicting": True},
        _tr("Yes, we take Northline Health.", "Actually I'm not sure, maybe we stopped."),
    )
    assert att["verdict"] == "UNCLEAR"
    assert "CONFLICTING" in att["diagnostic_tags"]


def test_goal_and_schema_from_pack():
    goal = pcv.build_goal(PACK_OBJ, REC)
    assert "automated" in goal.lower() and "Northline Health plan" in goal
    schema = pcv.build_result_schema(PACK_OBJ)
    assert schema["properties"]["accepts_plan"]["enum"] == ["yes", "no", "unknown"]


def test_raw_calltask_transcript_is_parsed():
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("_verdict_cli", SKILL / "scripts" / "verdict.py")
    m = module_from_spec(spec)
    spec.loader.exec_module(m)
    calltask = {
        "recipients": [
            {"attempts": [{"transcript_turns": [
                {"speaker": "user", "text": "No, we dropped Northline Health in March."}
            ]}]}
        ]
    }
    turns = m._turns(calltask)
    assert turns and turns[0]["text"].startswith("No, we dropped")


@pytest.mark.parametrize("claim_id", ["accepts_plan", "accepting_new_patients", "address_current"])
def test_pack_claims_have_guidance(claim_id):
    assert pcv.get_claim(PACK_OBJ, claim_id)["answer_guidance"]
