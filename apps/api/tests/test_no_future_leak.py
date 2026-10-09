"""State and intelligence at time t must be a function of events <= t only."""
from __future__ import annotations

import pytest

from rely_brain.orchestrator import run_pipeline
from rely_brain.state import compute_state
from rely_brain.turning_points import detect

from .conftest import truncated

UNTILS = [0, 45, 900, 2699, 2700, 3365, 3600, 3661, 4800, 5400]


@pytest.mark.parametrize("until", UNTILS)
def test_state_equals_truncated_stream(demo, until):
    a = compute_state(demo, until).model_dump()
    b = compute_state(truncated(demo, until), until).model_dump()
    assert a == b


@pytest.mark.parametrize("until", UNTILS)
def test_no_reference_to_future_events(demo, until):
    ids_after = {e.event_id for e in demo.events if e.match_second > until}
    st = compute_state(demo, until)
    assert not ({e.event_id for e in st.recent_events + st.current_sequence} & ids_after)
    for m in detect(demo, until):
        assert m.detected_at <= until
        assert not (set(m.linked_event_ids) & ids_after)
        for ev in m.evidence:
            assert not (set(ev.event_ids) & ids_after)
        for w in (m.before_state, m.after_state):
            if w is not None:
                assert w.end <= until + 1


def test_agent_claims_only_reference_past(demo):
    until = 3700
    s = run_pipeline(demo, until)
    ids_after = {e.event_id for e in demo.events if e.match_second > until}
    for c in s.claims:
        assert not (set(c.event_ids) & ids_after)
        assert all(t <= until for t in c.timestamps)


def test_future_change_does_not_alter_past_state(demo):
    """Tamper with every event after t: the state at t must not change."""
    until = 3000
    tampered = demo.model_copy(update={"events": [e if e.match_second <= until else e.model_copy(update={"event_type": "Shot", "outcome": "Goal"})
                                                  for e in demo.events]})
    assert compute_state(tampered, until).model_dump() == compute_state(demo, until).model_dump()
