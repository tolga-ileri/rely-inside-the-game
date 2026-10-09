"""Match State engine: everything is recomputed from the events received so far (<= until)."""
from __future__ import annotations

import hashlib
import math
from collections import defaultdict

from .data import events_until
from .schemas import Event, Match, MatchState, PlayerInvolvement, SequenceSummary, TeamStats
from .windows import BOX_X, FINAL_THIRD, channel, is_box_entry, is_entry, is_progressive, is_recovery, window_metrics

MOMENTUM_ALPHA = 0.25
MOMENTUM_SCALE = 5.0


def clock_label(sec: int) -> str:
    return f"{sec // 60:02d}:{sec % 60:02d}"


def threat_by_minute(events: list[Event], team_id: str, minutes: int) -> list[float]:
    """Per-minute threat: entries 1, box entries 2, shots 3, high pressures 0.5, recoveries in opp half 0.5."""
    out = [0.0] * (minutes + 1)
    for e in events:
        if e.team_id != team_id:
            continue
        m = min(e.minute, minutes)
        if is_entry(e):
            out[m] += 1.0
        if is_box_entry(e):
            out[m] += 2.0
        if e.event_type == "Shot":
            out[m] += 3.0
        if e.event_type == "Pressure" and e.start_x >= 60:
            out[m] += 0.5
        if is_recovery(e) and e.start_x >= 50:
            out[m] += 0.5
    return out


def momentum_series(events: list[Event], home: str, away: str, until: int) -> list[float]:
    """Rely momentum: EWMA of (home threat - away threat) per minute, squashed to -100..100."""
    minutes = until // 60
    h = threat_by_minute(events, home, minutes)
    a = threat_by_minute(events, away, minutes)
    series, v = [], 0.0
    for i in range(minutes + 1):
        v = MOMENTUM_ALPHA * (h[i] - a[i]) + (1 - MOMENTUM_ALPHA) * v
        series.append(round(100 * math.tanh(v / MOMENTUM_SCALE), 1))
    return series


def compute_state(match: Match, until: int) -> MatchState:
    until = max(0, min(until, match.duration_seconds))
    evs = events_until(match, until)
    home, away = match.home_team_id, match.away_team_id
    names = match.player_names()
    stats = {tid: TeamStats(team_id=tid) for tid in (home, away)}
    completed = {home: 0, away: 0}
    touches: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    team_of: dict[str, str] = {}
    seqs: dict[int, SequenceSummary] = {}
    for e in evs:
        s = stats[e.team_id]
        t = e.event_type
        if e.player_id and t not in ("Substitution", "Card"):
            team_of[e.player_id] = e.team_id
            touches[e.player_id][0] += 1
        if t == "Pass":
            s.passes += 1
            if e.outcome == "Complete":
                completed[e.team_id] += 1
        if is_progressive(e):
            s.progressive_actions += 1
            if e.player_id:
                touches[e.player_id][1] += 1
        if is_entry(e):
            s.final_third_entries += 1
            s.entries_by_channel[channel(e.end_y or 50)] += 1
            if e.player_id:
                touches[e.player_id][2] += 1
        if is_box_entry(e):
            s.box_entries += 1
        if t == "Shot":
            s.shots += 1
            s.xg = round(s.xg + float(e.qualifiers.get("xg", 0)), 2)
            if e.outcome in ("Saved", "Goal"):
                s.shots_on_target += 1
        if t == "Goal":
            s.goals += 1
        if is_recovery(e):
            s.recoveries += 1
        if t == "Possession Change":
            stats[match.opponent(e.team_id)].turnovers += 1
        if t == "Pressure":
            s.pressures += 1
            if e.start_x >= 60:
                s.high_pressures += 1
        if t == "Foul":
            s.fouls += 1
        if t == "Card":
            if e.outcome == "Red":
                s.red_cards += 1
                s.players_on_pitch -= 1
            else:
                s.yellow_cards += 1
        if t == "Substitution":
            s.substitutions += 1
        if t not in ("Substitution", "Card"):
            sq = seqs.get(e.sequence_id)
            if sq is None:
                sq = seqs[e.sequence_id] = SequenceSummary(
                    sequence_id=e.sequence_id, possession_id=e.possession_id, team_id=e.team_id,
                    start_second=e.match_second, end_second=e.match_second, event_ids=[],
                    reached_final_third=False, reached_box=False, ended_in_shot=False)
            sq.end_second = e.match_second
            sq.event_ids.append(e.event_id)
            if e.team_id == sq.team_id:
                if (e.end_x or e.start_x) >= FINAL_THIRD:
                    sq.reached_final_third = True
                if is_box_entry(e) or (e.event_type == "Shot" and e.start_x >= BOX_X - 10):
                    sq.reached_box = True
                if t == "Shot":
                    sq.ended_in_shot = True
    tot = completed[home] + completed[away]
    for tid in (home, away):
        s = stats[tid]
        s.pass_accuracy = round(completed[tid] / s.passes, 3) if s.passes else 0.0
        s.possession = round(completed[tid] / tot, 3) if tot else 0.5
    period = 1 if until < 2700 else 2
    mseries = momentum_series(evs, home, away, until)
    involvement = sorted(
        (PlayerInvolvement(player_id=p, name=names.get(p, p), team_id=team_of[p], touches=v[0],
                           progressive_actions=v[1], final_third_entries=v[2]) for p, v in touches.items()),
        key=lambda x: (-x.touches, x.player_id))[:10]
    danger = [s for s in seqs.values() if s.reached_box or s.ended_in_shot][-8:]
    last_seq_id = next((e.sequence_id for e in reversed(evs) if e.event_type not in ("Substitution", "Card")), None)
    current_seq = [e for e in evs if e.sequence_id == last_seq_id][-14:] if last_seq_id is not None else []
    possession_team = next((e.team_id for e in reversed(evs) if e.event_type in ("Pass", "Carry", "Dribble", "Restart", "Ball Recovery", "Possession Change")), None)
    last5 = {tid: window_metrics(evs, tid, max(0, until - 300), until + 1) for tid in (home, away)}
    last10 = {tid: window_metrics(evs, tid, max(0, until - 600), until + 1) for tid in (home, away)}
    digest = hashlib.sha256(f"{match.match_id}|{len(evs)}|{evs[-1].event_id if evs else ''}".encode()).hexdigest()[:16]
    return MatchState(
        match_id=match.match_id, until=until, period=period, clock=clock_label(until), minute=until // 60,
        score={home: stats[home].goals, away: stats[away].goals}, possession_team_id=possession_team,
        teams=stats, momentum=mseries[-1] if mseries else 0.0, momentum_series=mseries,
        last5=last5, last10=last10, recent_events=evs[-12:], current_sequence=current_seq,
        player_involvement=involvement, sequences_total=len(seqs), dangerous_sequences=danger,
        events_processed=len(evs), is_full_time=until >= match.duration_seconds, is_half_time=2700 <= until < 2760,
        state_hash=digest,
    )
