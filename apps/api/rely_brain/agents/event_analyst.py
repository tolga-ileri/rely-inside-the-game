"""Event Analyst Agent: turns the live Match State into typed, metric-referenced Observations."""
from __future__ import annotations

from ..schemas import MetricRef, Observation
from .base import Agent, SharedState


class EventAnalystAgent(Agent):
    name = "event_analyst"

    def run(self, s: SharedState) -> int:
        if "event_analyst" in s.fail:
            raise RuntimeError("simulated Event Analyst failure")
        st = s.state
        assert st is not None
        m = s.match
        out: list[Observation] = []
        for tid in (m.home_team_id, m.away_team_id):
            name = m.team(tid).name
            l10, l5, tot = st.last10[tid], st.last5[tid], st.teams[tid]
            ch = max("LCR", key=lambda c: getattr(l10, f"entries_{c}"))
            out.append(Observation(
                id=f"obs-{tid}-entries", agent=self.name, team_id=tid,
                text=f"{name}: {l10.final_third_entries} final-third entries in the last 10' (L {l10.entries_L} / C {l10.entries_C} / R {l10.entries_R}).",
                metrics=[MetricRef(path=f"state.last10.{tid}.final_third_entries", value=l10.final_third_entries),
                         MetricRef(path=f"state.last10.{tid}.entries_{ch}", value=getattr(l10, f"entries_{ch}"))],
                event_ids=l10.event_ids[-8:], timestamps=[st.until]))
            out.append(Observation(
                id=f"obs-{tid}-shots", agent=self.name, team_id=tid,
                text=f"{name}: {tot.shots} shots ({tot.shots_on_target} on target), {l10.shots} in the last 10'.",
                metrics=[MetricRef(path=f"state.teams.{tid}.shots", value=tot.shots),
                         MetricRef(path=f"state.teams.{tid}.shots_on_target", value=tot.shots_on_target),
                         MetricRef(path=f"state.last10.{tid}.shots", value=l10.shots)]))
            out.append(Observation(
                id=f"obs-{tid}-press", agent=self.name, team_id=tid,
                text=f"{name}: {l5.high_pressures} high pressures and {l5.recoveries} recoveries in the last 5'.",
                metrics=[MetricRef(path=f"state.last5.{tid}.high_pressures", value=l5.high_pressures),
                         MetricRef(path=f"state.last5.{tid}.recoveries", value=l5.recoveries)]))
            out.append(Observation(
                id=f"obs-{tid}-share", agent=self.name, team_id=tid,
                text=f"{name}: {round(l10.pass_share * 100)}% of completed passes in the last 10'.",
                metrics=[MetricRef(path=f"state.last10.{tid}.pass_share", value=l10.pass_share)]))
        out.append(Observation(
            id="obs-momentum", agent=self.name,
            text=f"Rely momentum {st.momentum:+.0f} ({'home' if st.momentum >= 0 else 'away'} side).",
            metrics=[MetricRef(path="state.momentum", value=st.momentum)]))
        if st.player_involvement:
            top = st.player_involvement[0]
            out.append(Observation(
                id="obs-involvement", agent=self.name, team_id=top.team_id,
                text=f"Most involved: {top.name} ({top.touches} actions).", player_ids=[top.player_id],
                metrics=[MetricRef(path=f"state.player.{top.player_id}.touches", value=top.touches)]))
        s.observations = list(out)
        return len(out)
