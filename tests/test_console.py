"""The web console over the same engine — smoke + the manual-entry / replay paths."""

import pytest
from fastapi.testclient import TestClient

from ghostline.console.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    j = client.get("/health").json()
    assert j["status"] == "ok"
    assert "healthcare@1" in j["packs"]


def test_index_renders_form(client):
    r = client.get("/")
    assert r.status_code == 200
    assert 'action="/verify"' in r.text
    assert "asserted" in r.text  # lifecycle line


def test_replay_all_runs_nine_scenarios(client):
    r = client.get("/replay", follow_redirects=False)
    assert r.status_code == 303
    run_id = r.headers["location"].split("/")[-1]
    j = client.get(f"/api/run/{run_id}").json()
    assert j["status"] == "done"
    verdicts = [v["verdict"] for rr in j["records"] for v in rr["verdicts"]]
    assert verdicts.count("NO_CONTACT") == 4
    assert verdicts.count("UNCLEAR") == 3
    assert "MATCH" in verdicts and "MISMATCH" in verdicts


def test_single_scenario_unclear_generic(client):
    r = client.get("/replay/03_unclear_generic", follow_redirects=False)
    run_id = r.headers["location"].split("/")[-1]
    j = client.get(f"/api/run/{run_id}").json()
    v = j["records"][0]["verdicts"][0]
    assert v["verdict"] == "UNCLEAR"
    assert "AMBIGUOUS" in v["tags"]


def test_corrections_csv_download(client):
    r = client.get("/replay", follow_redirects=False)
    run_id = r.headers["location"].split("/")[-1]
    csv_resp = client.get(f"/run/{run_id}/corrections.csv")
    assert csv_resp.headers["content-type"].startswith("text/csv")
    lines = [ln for ln in csv_resp.text.strip().splitlines() if ln]
    assert len(lines) == 2  # header + the one MISMATCH
    assert "MISMATCH" in lines[1]


def test_live_mode_without_record_redirects_with_error(client):
    r = client.post("/verify", data={"mode": "live", "pack": "healthcare"}, follow_redirects=False)
    assert r.status_code == 303
    assert "error" in r.headers["location"]
