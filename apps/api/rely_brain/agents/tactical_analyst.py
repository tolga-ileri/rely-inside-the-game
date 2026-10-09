"""Tactical Analyst Agent: interprets detected moments into Patterns, Findings, Hypotheses,
Recommendations and Risks. It never invents moments; it only reasons over detector output."""
from __future__ import annotations

from ..schemas import Claim, Finding, Hypothesis, MatchMoment, MetricRef, Pattern, Recommendation, Risk
from ..turning_points import CH_NAME
from .base import Agent, SharedState

HYPOTHESIS = {
    "sub_shift": ("The substitution changed where {team} progress: the new player's side is now the main route forward.",
                  "Event data has no off-ball tracking; the positional mechanism is inferred from on-ball events."),
    "red_card": ("With a player fewer, {team} defend deeper and concede territory.",
                 "Other factors (score, fatigue) also change behaviour after a red card."),
    "shot_surge": ("{team} are generating repeated chances, not a single burst.", "Shot volume is not shot quality; check xG."),
    "momentum_swing": ("{team} are winning the ball higher and reaching the final third more often.",
                       "Momentum is a composite of event counts and can swing back quickly."),
    "channel_dominance": ("{team} have found a repeatable route forward on one side.", "Small samples: one 10' window."),
    "possession_swing": ("{team} have taken control of the ball.", "Pass share is a proxy for possession time."),
    "dangerous_sequences": ("{team} are arriving in the box repeatedly.", "Box arrivals do not guarantee shots on target."),
}
REC = {
    "sub_shift": ("Keep loading the {ch} side and add a runner from midfield.", "Shift the block towards the {ch} side and double up."),
    "red_card": ("Settle into a compact 4-4-1 and defend the box.", "Stretch the ten men: switch play quickly and attack wide."),
    "shot_surge": ("Keep numbers around the box for second balls.", "Slow the game down and win second balls."),
    "momentum_swing": ("Press while momentum is high.", "Break the rhythm with longer possessions."),
    "channel_dominance": ("Keep isolating that side, vary the final ball.", "Shift the block to the {ch} side."),
    "possession_swing": ("Use the ball to pin the opponent back.", "Compress the centre and press the first pass."),
    "dangerous_sequences": ("Keep committing numbers to the box.", "Defend the box with more bodies."),
}
KEY_FIELDS = {
    "sub_shift": ["prog_share_{channel}", "shots", "box_entries"],
    "red_card": ["pass_share", "final_third_share", "final_third_entries"],
    "shot_surge": ["shots", "xg"],
    "momentum_swing": ["final_third_entries", "high_pressures", "recoveries"],
    "channel_dominance": ["entries_{channel}", "final_third_entries"],
    "possession_swing": ["pass_share"],
    "dangerous_sequences": ["dangerous_sequences", "box_entries"],
}


def _field_value(m: MatchMoment, which: str, fld: str):
    w = m.before_state if which == "before" else m.after_state
    if w is None:
        return None
    if fld.startswith("prog_share_"):
        return round(w.prog_share(fld[-1]), 3)
    return getattr(w, fld)


class TacticalAnalystAgent(Agent):
    name = "tactical_analyst"

    def run(self, s: SharedState) -> int:
        if "tactical_analyst" in s.fail:
            raise RuntimeError("simulated Tactical Analyst failure")
        m = s.match
        moments = [x for x in s.moments if x.type != "goal"]
        focus = s.focus()
        chosen = moments[-3:]
        if focus and focus.type != "goal" and focus not in chosen:
            chosen.append(focus)
        out: list[Claim] = []
        for mm in chosen:
            team = m.team(mm.team_id).name
            opp_id = m.opponent(mm.team_id)
            ch = mm.params.get("channel", "C")
            fmt = {"team": team, "ch": CH_NAME.get(ch, "centre")}
            fields = [f.format(channel=ch) for f in KEY_FIELDS[mm.type]]
            refs: list[MetricRef] = []
            for which in ("before", "after"):
                for f in fields:
                    v = _field_value(mm, which, f)
                    if v is not None:
                        refs.append(MetricRef(path=f"moment.{mm.id}.{which}.{f}", value=v))
            players = [p for p in (mm.trigger.get("player_id"), mm.trigger.get("player_in")) if p]
            base = dict(team_id=mm.team_id, moment_id=mm.id, event_ids=mm.linked_event_ids[:10], timestamps=[mm.timestamp])
            out.append(Pattern(id=f"pat-{mm.id}", agent=self.name, text=mm.title, metrics=refs[:2], **base))
            deltas = []
            for f in fields:
                b, a = _field_value(mm, "before", f), _field_value(mm, "after", f)
                if b is not None and a is not None:
                    deltas.append(f"{f.replace('_', ' ')} {b} -> {a}")
            out.append(Finding(id=f"fnd-{mm.id}", agent=self.name, text=f"{team}: " + "; ".join(deltas), metrics=refs,
                               player_ids=players, **base))
            hyp, caveat = HYPOTHESIS[mm.type]
            out.append(Hypothesis(id=f"hyp-{mm.id}", agent=self.name, text=hyp.format(**fmt), caveat=caveat,
                                  confidence=mm.confidence, metrics=refs[-2:], **base))
            r_team, r_opp = REC[mm.type]
            out.append(Recommendation(id=f"rec-{mm.id}-team", agent=self.name, text=f"{team}: " + r_team.format(**fmt),
                                      metrics=refs[-2:], **base))
            out.append(Recommendation(id=f"rec-{mm.id}-opp", agent=self.name, text=f"{m.team(opp_id).name}: " + r_opp.format(**fmt),
                                      metrics=refs[-2:], **{**base, "team_id": opp_id}))
            if mm.type in ("sub_shift", "channel_dominance") and mm.after_state is not None:
                aw = mm.after_state
                path = f"window.{opp_id}.{aw.start}.{aw.end}.shots"
                st = s.state
                assert st is not None
                from ..data import events_until
                from ..windows import window_metrics
                opp_shots = window_metrics(events_until(m, st.until), opp_id, aw.start, aw.end).shots
                out.append(Risk(id=f"risk-{mm.id}", agent=self.name,
                                text=f"Rest defence: {m.team(opp_id).name} have {opp_shots} shots in the same window; watch the space behind the advanced full-back.",
                                metrics=[MetricRef(path=path, value=opp_shots)], **base))
        s.tactical = out
        return len(out)
