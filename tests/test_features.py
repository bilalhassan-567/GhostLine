"""Derived calls, pack generator, benchmark, duplicate-number guard, webhook resolution."""

from ghostline.benchmark import run_replay_benchmark
from ghostline.derived import detect
from ghostline.models import CallOutcome, Record, Speaker, Transcript, TranscriptTurn
from ghostline.pack_generator import draft_pack


def _convo(*users):
    turns = [TranscriptTurn(speaker=Speaker.BOT, text="Do you accept the plan?")]
    turns += [TranscriptTurn(speaker=Speaker.USER, text=u) for u in users]
    return Transcript(call_id="c", outcome=CallOutcome.CONVERSATION, turns=turns)


# --- derived calls ---
def test_derived_detects_new_contact():
    p = detect(_convo("For plan questions you'd want to talk to Sarah in billing now."))
    assert p and p.kind == "contact" and "Sarah" in p.detail


def test_derived_detects_move():
    p = detect(_convo("We moved to Lakeside Plaza in the spring."))
    assert p and p.kind == "moved"


def test_derived_surfaces_number_but_does_not_autodial():
    p = detect(_convo("You want our other office, call them at +1 202 555 0199 instead."))
    assert p and p.kind == "number"
    assert p.phone == "+12025550199"  # surfaced as a suggestion, requires approval


def test_no_lead_no_proposal():
    assert detect(_convo("Yes, we take that plan.")) is None


# --- pack generator (no LLM key -> deterministic template) ---
def test_generate_pack_from_sentence():
    pack = draft_pack("verify these restaurants are still open at the address on file")
    assert pack.claims
    assert pack.expires_after_days == 30  # "open" -> short recheck
    assert pack.claims[0].question.endswith("?")


def test_generate_pack_insurance_gets_90_day_window():
    pack = draft_pack("check these clinics still accept the plan")
    assert pack.expires_after_days == 90


# --- benchmark ---
def test_replay_benchmark_shape():
    r = run_replay_benchmark()
    assert r["mode"] == "replay"
    assert r["n_calls"] == 9
    assert 0.0 <= r["human_agreement_rate"] <= 1.0
    assert "failure_taxonomy" in r
    assert "fixture" in r["note"].lower()


# --- duplicate-number guard ---
def test_duplicate_number_guard():
    from ghostline.console.runs import duplicate_number_groups

    recs = [
        Record(record_id="a", name="A", phone="+12025550110", claims={}),
        Record(record_id="b", name="B", phone="+12025550110", claims={}),
        Record(record_id="c", name="C", phone="+12025550120", claims={}),
    ]
    groups = duplicate_number_groups(recs)
    assert groups == [["a", "b"]]


# --- webhook resolution + kv round-trip ---
def test_webhook_resolution_and_kv_roundtrip():
    from ghostline.console import runs, store_kv

    rec = Record(record_id="w1", name="W", phone="+12025550142", region="US",
                 claims={"accepts_plan": True})
    run = runs.Run(id="wtest", mode="live", pack_ref="healthcare")
    run.records = [runs.RecordRun(record=rec, status="dialing", dial_e164="+12025550142")]
    runs._RUNS["wtest"] = run
    store_kv.save(run)
    assert store_kv.load("wtest").records[0].record.name == "W"

    calltask = {"id": "call_x", "status": "completed", "recipients": [{"attempts": [{
        "status": "completed", "transcript_turns": [
            {"speaker": "user", "text": "Yes, we accept Northline Health, always have."}]}]}]}
    runs.resolve_from_webhook("wtest", 0, calltask)
    rr = runs.get_run("wtest").records[0]
    assert rr.status == "done"
    assert rr.attestations[0].verdict.value == "MATCH"


def test_webhook_rejected_when_not_configured():
    from fastapi.testclient import TestClient

    from ghostline.console.app import app

    r = TestClient(app).post("/calle/webhook", json={"data": {}})
    assert r.status_code == 404  # webhook_base not set -> unsolicited posts rejected


def test_kv_key_is_sanitised():
    from ghostline.console import store_kv

    assert store_kv._key("../../etc/passwd") == "gl:run:etcpasswd"
    assert store_kv._key("abc-123_XYZ") == "gl:run:abc-123_XYZ"


def test_reverification_diff_fires_when_verdict_changes():
    from ghostline.console import runs
    from ghostline.models import Attestation, Verdict
    from ghostline.store import Ledger

    rid = "diff_rx_" + str(id(object()))  # unique so prior runs don't pollute
    led = Ledger()
    led.record(
        Attestation(record_id=rid, claim_id="accepts_plan", pack_ref="healthcare@1",
                    verdict=Verdict.MATCH, answer_text="yes we take it", evidence_span="x"),
        phone_e164="+12025550110",
    )
    led.close()

    run = runs.Run(id="diffrun", mode="live", pack_ref="healthcare")
    rr = runs.RecordRun(record=Record(record_id=rid, name="X", phone="+12025550110", claims={}))
    rr.attestations = [
        Attestation(record_id=rid, claim_id="accepts_plan", pack_ref="healthcare@1",
                    verdict=Verdict.MISMATCH, answer_text="no we dropped it", evidence_span="y")
    ]
    run.records = [rr]
    runs._attach_diff(run)
    assert rr.diff and rr.diff[0]["was"] == "MATCH" and rr.diff[0]["now"] == "MISMATCH"
