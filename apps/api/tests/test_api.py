from __future__ import annotations

from fastapi.testclient import TestClient

from rely_brain.api import app

c = TestClient(app)
MID = "hcf-wva-tactical-shift"


def test_health_ready():
    assert c.get("/health").json() == {"status": "ok"}
    r = c.get("/ready").json()
    assert r["ready"] and r["matches"] == 5 and r["ai_provider"] == "none"


def test_match_meta_has_no_events_and_label():
    d = c.get(f"/api/matches/{MID}").json()
    assert "events" not in d and d["data_label"] == "SYNTHETIC FOOTBALL-REALISTIC DATA"
    assert c.get("/api/matches/nope").status_code == 404


def test_live_and_keymoments():
    km = c.get(f"/api/matches/{MID}/keymoments").json()
    head = km["headline"]
    r = c.get(f"/api/matches/{MID}/live", params={"until": head["detected_at"]}).json()
    assert r["headline_id"] == head["id"]
    assert r["state"]["until"] == head["detected_at"]
    assert r["feed"] and r["trace"] and r["verification"]["coverage"] > 0


def test_explain_personas_and_locales():
    for persona in ("coach", "analyst", "broadcaster", "fan"):
        for loc in ("en", "tr", "es"):
            r = c.get(f"/api/matches/{MID}/explain", params={"until": 3700, "persona": persona, "locale": loc})
            assert r.status_code == 200
            j = r.json()
            assert j["narrative"]["persona"] == persona and j["events"]
    assert c.get(f"/api/matches/{MID}/explain", params={"until": 3700, "persona": "pundit"}).status_code == 422


def test_explain_reports_unavailable_on_narrative_failure():
    j = c.get(f"/api/matches/{MID}/explain", params={"until": 3700, "fail": "narrative"}).json()
    assert j["narrative"] is None and j["explanation_unavailable"]
    assert j["moment"]["explanation_status"] == "unavailable" and j["claims"]


def test_response_whatif_recap():
    r = c.post(f"/api/matches/{MID}/response", json={"until": 3700}).json()
    assert r["from_shape"] == "4-3-3" and r["to_shape"] == "3-2-5" and r["team_id"] == "HCF"
    roles = {p["role"] for p in r["players"] if p["moves"]}
    assert {"RB", "LB", "RCM", "RW"} <= roles
    assert r["risk"] and r["instruction"] and r["formation_impact"]["back_line"] == [4, 3]
    w = c.post(f"/api/matches/{MID}/whatif", json={"until": 3700, "option": "counter_5_4_1", "locale": "es"}).json()
    assert w["score_prediction"] is None and w["limitations"] and w["players"]
    assert c.post(f"/api/matches/{MID}/whatif", json={"until": 3700, "option": "x"}).status_code == 422
    rc = c.get(f"/api/matches/{MID}/recap", params={"until": 5400, "locale": "tr"}).json()
    assert rc["status"] == "Maç sonu" and rc["social"]


def test_stream_endpoint_template_mode():
    r = c.get(f"/api/matches/{MID}/explain/stream", params={"until": 3700})
    assert r.status_code == 200 and "event: final" in r.text
