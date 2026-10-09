"""Metric definitions and rolling windows. All metrics derive from events only.

Definitions (acting team's attacking frame, x: 0 own goal -> 100 opponent goal):
- final-third entry: completed Pass/Carry/Dribble/Cross starting x < 66.7 and ending x >= 66.7;
  channel from end_y (L < 33.3 <= C <= 66.7 < R)
- progressive action: completed Pass/Carry/Dribble moving the ball >= 10 units forward
- box entry: completed Pass/Carry/Dribble/Cross ending x >= 83, 21 <= y <= 79
- recovery: Ball Recovery, Interception, or Tackle won
- turnover: a Possession Change to the opponent
- high pressure: Pressure with start_x >= 60 (in the opponent half)
- pass share: team's completed passes / all completed passes in the window (possession proxy)
- dangerous sequence: a sequence reaching the box or ending in a shot
"""
from __future__ import annotations

from collections.abc import Iterable

from .schemas import Event, WindowMetrics

FINAL_THIRD = 66.7
BOX_X = 83.0
MOVE_TYPES = {"Pass", "Carry", "Dribble", "Cross"}
COMPLETE = {"Complete"}


def channel(y: float) -> str:
    return "L" if y < 33.34 else ("R" if y > 66.66 else "C")


def is_completed_move(e: Event) -> bool:
    if e.event_type not in MOVE_TYPES or e.end_x is None:
        return False
    return e.event_type == "Carry" or e.outcome in COMPLETE


def is_entry(e: Event) -> bool:
    return is_completed_move(e) and e.start_x < FINAL_THIRD <= (e.end_x or 0)


def is_box_entry(e: Event) -> bool:
    return is_completed_move(e) and (e.end_x or 0) >= BOX_X and 21 <= (e.end_y or 0) <= 79 and e.start_x < BOX_X


def is_progressive(e: Event) -> bool:
    return is_completed_move(e) and (e.end_x or 0) - e.start_x >= 10


def is_recovery(e: Event) -> bool:
    return e.event_type in ("Ball Recovery", "Interception") or (e.event_type == "Tackle" and e.outcome == "Won")


def window_metrics(events: Iterable[Event], team_id: str, start: int, end: int) -> WindowMetrics:
    c = dict.fromkeys(("passes", "passes_completed", "progressive_actions", "prog_L", "prog_C", "prog_R",
                       "final_third_entries", "entries_L", "entries_C", "entries_R", "box_entries", "shots",
                       "shots_on_target", "goals", "recoveries", "turnovers", "pressures", "high_pressures"), 0)
    xg = 0.0
    total_completed = 0
    team_ft_actions = 0
    all_ft_actions = 0
    seqs: set[int] = set()
    ids: list[str] = []
    for e in events:
        if not (start <= e.match_second < end):
            continue
        t = e.event_type
        if t == "Pass" and e.outcome == "Complete":
            total_completed += 1
        if t in MOVE_TYPES and e.end_x is not None and e.end_x >= FINAL_THIRD and is_completed_move(e):
            all_ft_actions += 1
            if e.team_id == team_id:
                team_ft_actions += 1
        if t == "Possession Change":
            if e.team_id != team_id:
                c["turnovers"] += 1
            continue
        if e.team_id != team_id:
            continue
        if t == "Pass":
            c["passes"] += 1
            if e.outcome == "Complete":
                c["passes_completed"] += 1
        if is_progressive(e):
            c["progressive_actions"] += 1
            c["prog_" + channel(e.end_y or 50)] += 1
        if is_entry(e):
            c["final_third_entries"] += 1
            c["entries_" + channel(e.end_y or 50)] += 1
            ids.append(e.event_id)
        if is_box_entry(e):
            c["box_entries"] += 1
            seqs.add(e.sequence_id)
        if t == "Shot":
            c["shots"] += 1
            if e.outcome in ("Saved", "Goal"):
                c["shots_on_target"] += 1
            xg += float(e.qualifiers.get("xg", 0))
            seqs.add(e.sequence_id)
            ids.append(e.event_id)
        elif t == "Goal":
            c["goals"] += 1
        elif t == "Pressure":
            c["pressures"] += 1
            if e.start_x >= 60:
                c["high_pressures"] += 1
        if is_recovery(e):
            c["recoveries"] += 1
    return WindowMetrics(
        team_id=team_id, start=start, end=end, **c, xg=round(xg, 2),
        pass_share=round(c["passes_completed"] / total_completed, 3) if total_completed else 0.0,
        final_third_share=round(team_ft_actions / all_ft_actions, 3) if all_ft_actions else 0.0,
        dangerous_sequences=len(seqs), event_ids=ids[-40:])


def before_after(events: list[Event], team_id: str, pivot: int, until: int, width: int = 600) -> tuple[WindowMetrics, WindowMetrics, bool]:
    """Symmetric windows around `pivot`; the after window is truncated at `until` (no future data)."""
    before = window_metrics(events, team_id, max(0, pivot - width), pivot)
    end = min(pivot + width, until + 1)
    after = window_metrics(events, team_id, pivot, end)
    return before, after, until + 1 >= pivot + width
