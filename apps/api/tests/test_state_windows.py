from __future__ import annotations

import json
from pathlib import Path

import pytest

from rely_brain.data import load_match
from rely_brain.schemas import EVENT_TYPES, Event
from rely_brain.state import compute_state
from rely_brain.windows import before_after, window_metrics

from .conftest import ALL

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("mid", ALL)
def test_matches_validate_and_are_synthetic(mid):
    m = load_match(mid)
    assert m.synthetic and "Synthetic" in m.data_statement
    assert m.event_count == len(m.events) > 1500
    secs = [e.match_second for e in m.events]
    assert secs == sorted(secs)
    assert len({e.event_id for e in m.events}) == len(m.events)
    assert {e.event_type for e in m.events} <= set(EVENT_TYPES)


def test_all_event_types_present(demo):
    assert {e.event_type for e in demo.events} == set(EVENT_TYPES)


def test_json_schema_file_matches_model():
    from scripts.export_schema import schemas

    on_disk = json.loads((ROOT / "synthetic-data" / "schemas" / "event.schema.json").read_text(encoding="utf-8"))
    assert on_disk == schemas()["event.schema.json"]
    for f in ("event_id", "match_id", "period", "match_second", "minute", "second", "team_id", "player_id", "event_type",
              "outcome", "start_x", "start_y", "end_x", "end_y", "possession_id", "sequence_id", "qualifiers", "metadata"):
        assert f in on_disk["properties"]


def test_generator_is_deterministic():
    import sys

    sys.path.insert(0, str(ROOT / "synthetic-data" / "generators"))
    from generate import generate

    a = generate("tactical_shift")
    on_disk = json.loads((ROOT / "synthetic-data" / "matches" / "hcf-wva-tactical-shift.json").read_text(encoding="utf-8"))
    assert a["events"] == on_disk["events"]


def test_full_time_score_matches_goal_events(demo):
    st = compute_state(demo, demo.duration_seconds)
    for tid in (demo.home_team_id, demo.away_team_id):
        assert st.score[tid] == sum(1 for e in demo.events if e.event_type == "Goal" and e.team_id == tid)
    assert st.is_full_time and st.events_processed == len(demo.events)


def test_state_counts(demo):
    st = compute_state(demo, 3000)
    h = st.teams[demo.home_team_id]
    evs = [e for e in demo.events if e.match_second <= 3000]
    assert h.shots == sum(1 for e in evs if e.event_type == "Shot" and e.team_id == demo.home_team_id)
    assert sum(h.entries_by_channel.values()) == h.final_third_entries
    assert abs(st.teams[demo.home_team_id].possession + st.teams[demo.away_team_id].possession - 1) < 0.01
    assert -100 <= st.momentum <= 100 and len(st.momentum_series) == 3000 // 60 + 1
    assert st.clock == "50:00" and st.period == 2
    assert all(e.match_second <= 3000 for e in st.recent_events + st.current_sequence)


def test_red_card_reduces_players(red):
    st = compute_state(red, 2400)
    assert st.teams["ELT"].red_cards == 1 and st.teams["ELT"].players_on_pitch == 10


def test_windows_last5_last10(demo):
    st = compute_state(demo, 3600)
    for tid in st.teams:
        assert st.last10[tid].start == 3000 and st.last5[tid].start == 3300
        assert st.last10[tid].shots >= st.last5[tid].shots
        assert st.last10[tid].entries_L + st.last10[tid].entries_C + st.last10[tid].entries_R == st.last10[tid].final_third_entries


def test_before_after_never_passes_until(demo):
    b, a, complete = before_after(demo.events, "HCF", 3360, 3500)
    assert a.end == 3501 and not complete
    b2, a2, complete2 = before_after(demo.events, "HCF", 3360, 5400)
    assert a2.end == 3960 and complete2
    assert window_metrics(demo.events, "HCF", 0, 5401).shots == compute_state(demo, 5400).teams["HCF"].shots


def test_event_model_rejects_bad_types():
    with pytest.raises(ValueError):
        Event(event_id="x", match_id="m", period=1, match_second=1, minute=0, second=1, team_id="A", event_type="Teleport",
              start_x=1, start_y=1, possession_id=1, sequence_id=1)
