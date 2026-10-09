from __future__ import annotations

import pytest

from rely_brain.data import load_match
from rely_brain.state import compute_state
from rely_brain.turning_points import detect, headline_moment

from .conftest import ALL, truncated


def test_tactical_shift_sub_detected_with_right_channel(demo):
    ms = detect(demo, demo.duration_seconds)
    head = headline_moment(ms)
    assert head.type == "sub_shift" and head.team_id == "HCF" and head.params["channel"] == "R"
    assert head.params["player_in"] == "Kai Okafor"
    assert head.params["share_after"] - head.params["share_before"] >= 30
    assert head.params["shots_after"] > head.params["shots_before"]
    assert 3600 <= head.detected_at <= 3700
    assert head.before_state and head.after_state
    assert {"event", "window", "metric", "sequence"} <= {e.kind for e in head.evidence}
    assert head.trigger["event_id"] in head.linked_event_ids


def test_demo_turning_point_hits_25_to_35_seconds_of_playback(demo):
    head = headline_moment(detect(demo, demo.duration_seconds))
    start, speed = demo.demo["start_second"], demo.demo["speed"]
    seconds = (head.detected_at - start) / speed
    assert 25 <= seconds <= 35, seconds


def test_sub_shift_not_visible_before_detection(demo):
    head = headline_moment(detect(demo, demo.duration_seconds))
    before = detect(demo, head.detected_at - 1)
    assert head.id not in {m.id for m in before}
    assert head.id in {m.id for m in detect(demo, head.detected_at)}


def test_red_card_moment_shift(red):
    ms = detect(red, red.duration_seconds)
    rc = next(m for m in ms if m.type == "red_card")
    p = rc.params
    assert rc.team_id == "ELT" and rc.severity == "high"
    assert p["share_after"] > p["share_before"] and p["territory_after"] > p["territory_before"]
    assert p["press_after"] < p["press_before"]  # deeper block
    assert headline_moment(ms).id == rc.id
    # Red card is available the second it happens, with an open after window
    live = next(m for m in detect(red, rc.timestamp) if m.id == rc.id)
    assert not live.after_window_complete


def test_late_comeback_detected_before_the_goal(late):
    home = late.home_team_id
    first_goal = min(e.match_second for e in late.events if e.event_type == "Goal" and e.team_id == home)
    ms = detect(late, first_goal - 1)  # only data before the equaliser
    pre = [m for m in ms if m.team_id == home and m.type != "goal" and m.detected_at >= 4200]
    assert pre, "the surge must be flagged before the goal"
    assert compute_state(late, first_goal - 1).score[home] == 0
    st = compute_state(late, late.duration_seconds)
    assert st.score[home] > st.score[late.away_team_id]


@pytest.mark.parametrize("mid", ALL)
def test_moments_are_compact_and_well_formed(mid):
    m = load_match(mid)
    ms = detect(m, m.duration_seconds)
    non_goal = [x for x in ms if x.type != "goal"]
    assert 1 <= len(non_goal) <= 14  # intelligence, not spam
    for x in ms:
        assert 0 < x.confidence <= 1 and x.evidence and x.rule
        assert x.detected_at >= x.timestamp or x.type in ("goal",)


@pytest.mark.parametrize("until", [600, 2000, 3300, 3700, 4500, 5400])
def test_detection_identical_on_physically_truncated_stream(demo, until):
    a = [x.model_dump() for x in detect(demo, until)]
    b = [x.model_dump() for x in detect(truncated(demo, until), until)]
    assert a == b
