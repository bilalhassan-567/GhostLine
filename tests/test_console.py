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


def test_replay_all_renders_nine_scenarios(client):
    r = client.get("/replay")
    assert r.status_code == 200
    assert r.text.count('class="rec"') == 9  # one card per fixture
    assert r.text.count("NO_CONTACT") >= 4
    assert "MATCH" in r.text and "MISMATCH" in r.text


def test_single_scenario_unclear_generic(client):
    r = client.get("/replay/03_unclear_generic")
    assert r.status_code == 200
    assert "UNCLEAR" in r.text
    assert "AMBIGUOUS" in r.text
    assert "<mark>" not in r.text  # UNCLEAR has no evidence span to highlight


def test_replay_corrections_csv(client):
    r = client.get("/replay-corrections.csv")
    assert r.headers["content-type"].startswith("text/csv")
    lines = [ln for ln in r.text.strip().splitlines() if ln]
    assert len(lines) == 2  # header + the one MISMATCH
    assert "MISMATCH" in lines[1]


def test_live_mode_without_record_redirects_with_error(client):
    r = client.post("/verify", data={"mode": "live", "pack": "healthcare"}, follow_redirects=False)
    assert r.status_code == 303
    assert "error" in r.headers["location"]


def test_verify_replay_renders_result_directly(client):
    r = client.post(
        "/verify",
        data={"mode": "replay", "pack": "healthcare", "name": "Test Clinic",
              "phone": "+12025550142", "region": "US", "claim__accepts_plan": "yes"},
    )
    assert r.status_code == 200
    assert 'class="chip' in r.text


def test_live_disabled_on_serverless(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    import importlib

    from ghostline.console import app as app_module

    importlib.reload(app_module)
    c = TestClient(app_module.app)
    r = c.post("/verify", data={"mode": "live", "pack": "healthcare", "name": "X",
                                "phone": "+12025550142"})
    assert r.status_code == 503
    assert "replay mode" in r.text.lower()
    monkeypatch.delenv("VERCEL")
    importlib.reload(app_module)
