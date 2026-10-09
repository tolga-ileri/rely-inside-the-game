"""Orchestrator: Match State -> Event Analyst -> Tactical Analyst -> Evidence Verifier -> Narrative.

Per-agent recovery: each agent runs in its own try/except. If Tactical fails, Event output remains;
if the Verifier fails, claims are returned unverified (coverage = null); if Narrative fails, the
structured intelligence remains and the moment is marked explanation_status="unavailable".
"""
from __future__ import annotations

import logging

from .agents.base import Agent, SharedState, Timer
from .agents.event_analyst import EventAnalystAgent
from .agents.narrative_agent import NarrativeAgent
from .agents.tactical_analyst import TacticalAnalystAgent
from .agents.verifier import EvidenceVerifierAgent
from .llm import LLMProvider, NoProvider
from .schemas import AgentTrace, Match
from .state import compute_state
from .turning_points import detect, headline_moment

log = logging.getLogger("rely.orchestrator")


def _run(agent: Agent, s: SharedState, provider_name: str, model: str | None) -> bool:
    t = Timer()
    status, outputs, note = "ok", 0, None
    with t:
        try:
            outputs = agent.run(s)
        except Exception as exc:  # per-agent recovery
            status, note = "failed", f"{type(exc).__name__}: {exc}"
            log.warning("agent_failed", extra={"agent": agent.name, "error": note})
    fallback = bool(getattr(agent, "fallback_used", False))
    if status == "ok" and fallback:
        status = "fallback"
    note = note or getattr(agent, "note", None)
    cov = s.verification.coverage if agent.name == "evidence_verifier" and s.verification else None
    s.trace.append(AgentTrace(agent=agent.name, status=status, ms=t.ms,  # type: ignore[arg-type]
                              provider=provider_name if agent.uses_llm else "deterministic",
                              model=model if agent.uses_llm else None, fallback_used=fallback,
                              evidence_coverage=cov, outputs=outputs, note=note))
    log.info("agent_run", extra={"agent": agent.name, "status": status, "ms": t.ms, "fallback": fallback})
    return status != "failed"


def run_pipeline(match: Match, until: int, persona: str = "analyst", locale: str = "en", moment_id: str | None = None,
                 with_narrative: bool = False, provider: LLMProvider | None = None, fail: set[str] | None = None) -> SharedState:
    provider = provider or NoProvider()
    s = SharedState(match=match, until=until, persona=persona, locale=locale, provider=provider, fail=set(fail or ()))
    with Timer() as t_state:
        s.state = compute_state(match, until)
    with Timer() as t_det:
        s.moments = detect(match, s.state.until)
    s.trace.append(AgentTrace(agent="match_state", status="ok", ms=t_state.ms, provider="deterministic",
                              outputs=s.state.events_processed))
    s.trace.append(AgentTrace(agent="turning_point_detector", status="ok", ms=t_det.ms, provider="deterministic",
                              outputs=len(s.moments)))
    log.info("state_computed", extra={"match_id": match.match_id, "until": until, "events": s.state.events_processed,
                                      "ms": t_state.ms, "detector_ms": t_det.ms})
    if moment_id and any(m.id == moment_id for m in s.moments):
        s.focus_moment_id = moment_id
    else:
        head = headline_moment(s.moments)
        s.focus_moment_id = head.id if head else None
    _run(EventAnalystAgent(), s, provider.name, provider.model)
    _run(TacticalAnalystAgent(), s, provider.name, provider.model)
    _run(EvidenceVerifierAgent(), s, provider.name, provider.model)
    if with_narrative:
        ok = _run(NarrativeAgent(), s, provider.name, provider.model)
        focus = s.focus()
        if not ok and focus is not None:
            focus.explanation_status = "unavailable"
            s.narrative = None
    return s
