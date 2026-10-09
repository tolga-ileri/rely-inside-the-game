"""Typed schemas shared by the match engine, agents and API."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EventType = Literal[
    "Pass", "Carry", "Shot", "Goal", "Ball Recovery", "Interception", "Tackle", "Pressure", "Duel", "Foul",
    "Card", "Substitution", "Clearance", "Cross", "Dribble", "Goalkeeper Action", "Possession Change", "Restart",
]
EVENT_TYPES: tuple[str, ...] = EventType.__args__  # type: ignore[attr-defined]
Channel = Literal["L", "C", "R"]
Persona = Literal["coach", "analyst", "broadcaster", "fan"]
Locale = Literal["en", "tr", "es"]
PERSONAS: tuple[str, ...] = ("coach", "analyst", "broadcaster", "fan")
LOCALES: tuple[str, ...] = ("en", "tr", "es")


class Event(BaseModel):
    """One on-ball or off-ball football event. Coordinates: 0-100, acting team's attacking frame."""

    model_config = ConfigDict(extra="forbid")
    event_id: str
    match_id: str
    period: int = Field(ge=1, le=2)
    match_second: int = Field(ge=0)
    minute: int = Field(ge=0)
    second: int = Field(ge=0, le=59)
    team_id: str
    player_id: str | None = None
    event_type: EventType
    outcome: str | None = None
    start_x: float = Field(ge=0, le=100)
    start_y: float = Field(ge=0, le=100)
    end_x: float | None = Field(default=None, ge=0, le=100)
    end_y: float | None = Field(default=None, ge=0, le=100)
    possession_id: int
    sequence_id: int
    qualifiers: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Player(BaseModel):
    player_id: str
    name: str
    number: int
    position: str
    starter: bool


class Team(BaseModel):
    side: Literal["home", "away"]
    team_id: str
    name: str
    short: str
    color: str
    crest: dict[str, str]
    players: list[Player]


class Match(BaseModel):
    match_id: str
    scenario: str
    title: str
    synthetic: bool = True
    data_statement: str
    duration_seconds: int
    demo: dict[str, Any] = Field(default_factory=dict)
    home_team_id: str
    away_team_id: str
    teams: list[Team]
    event_count: int
    events: list[Event]

    def team(self, team_id: str) -> Team:
        return next(t for t in self.teams if t.team_id == team_id)

    def opponent(self, team_id: str) -> str:
        return self.away_team_id if team_id == self.home_team_id else self.home_team_id

    def player_names(self) -> dict[str, str]:
        return {p.player_id: p.name for t in self.teams for p in t.players}


# ---------------------------------------------------------------- state
class WindowMetrics(BaseModel):
    """Team metrics over a half-open window [start, end) in match seconds."""

    team_id: str
    start: int
    end: int
    passes: int = 0
    passes_completed: int = 0
    pass_share: float = 0.0
    progressive_actions: int = 0
    prog_L: int = 0
    prog_C: int = 0
    prog_R: int = 0
    final_third_entries: int = 0
    entries_L: int = 0
    entries_C: int = 0
    entries_R: int = 0
    box_entries: int = 0
    shots: int = 0
    shots_on_target: int = 0
    xg: float = 0.0
    goals: int = 0
    recoveries: int = 0
    turnovers: int = 0
    pressures: int = 0
    high_pressures: int = 0
    dangerous_sequences: int = 0
    final_third_share: float = 0.0
    event_ids: list[str] = Field(default_factory=list, description="Sample of contributing event ids")

    def share(self, ch: str) -> float:
        n = self.final_third_entries
        return 0.0 if n == 0 else getattr(self, f"entries_{ch}") / n

    def prog_share(self, ch: str) -> float:
        n = self.progressive_actions
        return 0.0 if n == 0 else getattr(self, f"prog_{ch}") / n


class TeamStats(BaseModel):
    team_id: str
    goals: int = 0
    shots: int = 0
    shots_on_target: int = 0
    xg: float = 0.0
    passes: int = 0
    pass_accuracy: float = 0.0
    possession: float = 0.0
    progressive_actions: int = 0
    final_third_entries: int = 0
    entries_by_channel: dict[str, int] = Field(default_factory=lambda: {"L": 0, "C": 0, "R": 0})
    box_entries: int = 0
    recoveries: int = 0
    turnovers: int = 0
    pressures: int = 0
    high_pressures: int = 0
    fouls: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    substitutions: int = 0
    players_on_pitch: int = 11


class PlayerInvolvement(BaseModel):
    player_id: str
    name: str
    team_id: str
    touches: int
    progressive_actions: int
    final_third_entries: int


class SequenceSummary(BaseModel):
    sequence_id: int
    possession_id: int
    team_id: str
    start_second: int
    end_second: int
    event_ids: list[str]
    reached_final_third: bool
    reached_box: bool
    ended_in_shot: bool


class MatchState(BaseModel):
    match_id: str
    until: int
    period: int
    clock: str
    minute: int
    score: dict[str, int]
    possession_team_id: str | None
    teams: dict[str, TeamStats]
    momentum: float = Field(description="-100 (away) .. +100 (home)")
    momentum_series: list[float]
    last5: dict[str, WindowMetrics]
    last10: dict[str, WindowMetrics]
    recent_events: list[Event]
    current_sequence: list[Event]
    player_involvement: list[PlayerInvolvement]
    sequences_total: int
    dangerous_sequences: list[SequenceSummary]
    events_processed: int
    is_full_time: bool
    is_half_time: bool
    state_hash: str


# ---------------------------------------------------------------- intelligence
class Evidence(BaseModel):
    id: str
    kind: Literal["metric", "event", "sequence", "window", "rule"]
    label: str
    value: float | int | str | None = None
    unit: str | None = None
    metric_path: str | None = None
    event_ids: list[str] = Field(default_factory=list)
    timestamp: int | None = None
    window: tuple[int, int] | None = None


class MatchMoment(BaseModel):
    id: str
    timestamp: int
    minute: int
    detected_at: int
    type: Literal["sub_shift", "red_card", "shot_surge", "momentum_swing", "channel_dominance",
                  "possession_swing", "dangerous_sequences", "goal"]
    team_id: str
    severity: Literal["low", "medium", "high"]
    title: str
    title_key: str
    params: dict[str, Any] = Field(default_factory=dict)
    trigger: dict[str, Any]
    before_state: WindowMetrics | None = None
    after_state: WindowMetrics | None = None
    after_window_complete: bool = False
    evidence: list[Evidence]
    confidence: float
    linked_event_ids: list[str]
    explanation_status: Literal["pending", "generated", "fallback", "unavailable"] = "pending"
    rule: str


ClaimKind = Literal["observation", "pattern", "finding", "hypothesis", "recommendation", "risk", "scenario", "action"]


class MetricRef(BaseModel):
    path: str
    value: float | int | str


class Claim(BaseModel):
    """Base for Observation/Pattern/Finding/Hypothesis/Recommendation/Risk/Scenario/Action."""

    id: str
    kind: ClaimKind
    agent: str
    text: str
    team_id: str | None = None
    metrics: list[MetricRef] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    player_ids: list[str] = Field(default_factory=list)
    timestamps: list[int] = Field(default_factory=list)
    moment_id: str | None = None
    confidence: float | None = None
    caveat: str | None = None
    verified: bool | None = None
    verification_notes: list[str] = Field(default_factory=list)


class Observation(Claim):
    kind: ClaimKind = "observation"


class Pattern(Claim):
    kind: ClaimKind = "pattern"


class Finding(Claim):
    kind: ClaimKind = "finding"


class Hypothesis(Claim):
    kind: ClaimKind = "hypothesis"


class Recommendation(Claim):
    kind: ClaimKind = "recommendation"


class Risk(Claim):
    kind: ClaimKind = "risk"


class Scenario(Claim):
    kind: ClaimKind = "scenario"


class Action(Claim):
    kind: ClaimKind = "action"


class VerificationReport(BaseModel):
    total_claims: int
    supported: int
    rejected: int
    unverifiable: int
    coverage: float = Field(description="supported / total; honest, never forced to 1.0")
    issues: list[str] = Field(default_factory=list)


class NarrativeOut(BaseModel):
    headline: str
    explanation: str
    bullets: list[str] = Field(default_factory=list)
    persona: str
    locale: str
    source: Literal["llm", "template"]
    verified: bool
    numbers_used: list[str] = Field(default_factory=list)


class AgentTrace(BaseModel):
    agent: str
    status: Literal["ok", "fallback", "failed", "skipped"]
    ms: float
    provider: str
    model: str | None = None
    fallback_used: bool = False
    evidence_coverage: float | None = None
    outputs: int = 0
    note: str | None = None
