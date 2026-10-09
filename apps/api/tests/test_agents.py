from __future__ import annotations

from rely_brain.agents.base import SharedState
from rely_brain.agents.verifier import EvidenceVerifierAgent
from rely_brain.orchestrator import run_pipeline
from rely_brain.schemas import Finding, MetricRef, Recommendation

UNTIL = 3700


def test_pipeline_runs_all_agents(demo):
    s = run_pipeline(demo, UNTIL, with_narrative=True)
    agents = [t.agent for t in s.trace]
    assert agents == ["match_state", "turning_point_detector", "event_analyst", "tactical_analyst", "evidence_verifier", "narrative"]
    assert all(t.status == "ok" for t in s.trace)
    assert s.observations and s.tactical and s.narrative
    kinds = {c.kind for c in s.tactical}
    assert {"pattern", "finding", "hypothesis", "recommendation", "risk"} <= kinds
    assert s.focus().type == "sub_shift"


def test_evidence_coverage_is_honest(demo):
    s = run_pipeline(demo, UNTIL)
    v = s.verification
    assert v.total_claims == v.supported + v.rejected + v.unverifiable
    assert v.unverifiable >= 1  # hypotheses are causal, never counted as verified
    assert 0.5 < v.coverage < 1.0
    assert v.rejected == 0


def test_tactical_failure_keeps_event_output(demo):
    s = run_pipeline(demo, UNTIL, fail={"tactical_analyst"}, with_narrative=True)
    t = {x.agent: x for x in s.trace}
    assert t["tactical_analyst"].status == "failed"
    assert s.observations and not s.tactical
    assert t["evidence_verifier"].status == "ok" and s.narrative is not None


def test_narrative_failure_keeps_structured_intelligence(demo):
    s = run_pipeline(demo, UNTIL, fail={"narrative"}, with_narrative=True)
    assert s.narrative is None
    assert s.focus().explanation_status == "unavailable"
    assert s.tactical and s.verification is not None


def test_event_failure_does_not_stop_pipeline(demo):
    s = run_pipeline(demo, UNTIL, fail={"event_analyst"})
    assert not s.observations and s.tactical


def _shared(demo):
    s = run_pipeline(demo, UNTIL)
    return s


def test_verifier_rejects_wrong_metric(demo):
    s = _shared(demo)
    m = s.focus()
    bad = Finding(id="bad", agent="test", text="x", metrics=[MetricRef(path=f"moment.{m.id}.after.shots", value=99)])
    good = Finding(id="good", agent="test", text="x", metrics=[MetricRef(path=f"moment.{m.id}.after.shots", value=m.after_state.shots)])
    s.tactical = [bad, good]
    s.observations = []
    EvidenceVerifierAgent().run(s)
    assert s.verification.rejected == 1 and s.verification.supported == 1
    assert [c.id for c in s.tactical] == ["good"]


def test_verifier_rejects_future_event_and_unknown_player(demo):
    s = _shared(demo)
    future = next(e.event_id for e in demo.events if e.match_second > UNTIL)
    s.observations = []
    s.tactical = [Recommendation(id="f", agent="t", text="x", event_ids=[future]),
                  Recommendation(id="p", agent="t", text="x", player_ids=["HCF-99"]),
                  Recommendation(id="ts", agent="t", text="x", timestamps=[UNTIL + 10]),
                  Recommendation(id="w", agent="t", text="x", metrics=[MetricRef(path=f"window.HCF.3000.{UNTIL + 500}.shots", value=1)])]
    EvidenceVerifierAgent().run(s)
    assert s.verification.rejected == 4 and s.tactical == []


def test_text_grounding_and_entities(demo):
    s = SharedState(match=demo, until=UNTIL)
    facts = {"share_before": 25, "share_after": 83, "team": "Harbour City FC"}
    ok = EvidenceVerifierAgent.check_text(s, ["Harbour City FC went from 25% to 83% with Kai Okafor."], facts)
    assert ok == []
    bad = EvidenceVerifierAgent.check_text(s, ["Harbour City FC went from 25% to 91% thanks to John Smith."], facts)
    assert any("91" in i for i in bad) and any("John Smith" in i for i in bad)


def test_formations_are_not_treated_as_metrics(demo):
    s = SharedState(match=demo, until=UNTIL)
    assert EvidenceVerifierAgent.check_text(s, ["Move from 4-3-3 to 3-2-5."], {}) == []
    assert EvidenceVerifierAgent.check_text(s, ["Move to a 4-4-1 with 7 shots."], {}) == ["ungrounded number '7'"]
