"""Shared agent state. Agents read and write explicit, typed fields; nothing is passed implicitly."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..llm import LLMProvider, NoProvider
from ..schemas import AgentTrace, Claim, Match, MatchMoment, MatchState, NarrativeOut, VerificationReport


@dataclass
class SharedState:
    match: Match
    until: int
    persona: str = "analyst"
    locale: str = "en"
    state: MatchState | None = None
    moments: list[MatchMoment] = field(default_factory=list)
    focus_moment_id: str | None = None
    observations: list[Claim] = field(default_factory=list)          # Event Analyst
    tactical: list[Claim] = field(default_factory=list)              # Tactical Analyst
    verification: VerificationReport | None = None                   # Evidence Verifier
    narrative: NarrativeOut | None = None                            # Narrative Agent
    trace: list[AgentTrace] = field(default_factory=list)
    provider: LLMProvider = field(default_factory=NoProvider)
    fail: set[str] = field(default_factory=set)                      # fault injection for tests/demo

    @property
    def claims(self) -> list[Claim]:
        return [*self.observations, *self.tactical]

    def focus(self) -> MatchMoment | None:
        if self.focus_moment_id:
            return next((m for m in self.moments if m.id == self.focus_moment_id), None)
        return None


class Agent:
    name = "agent"
    uses_llm = False

    def run(self, s: SharedState) -> int:  # returns number of outputs
        raise NotImplementedError


class Timer:
    def __enter__(self) -> Timer:
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.ms = round((time.perf_counter() - self.t0) * 1000, 2)
