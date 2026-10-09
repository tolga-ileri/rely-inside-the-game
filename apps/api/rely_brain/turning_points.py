"""Deterministic turning-point detector (rules first, AI never decides what a turning point is).

Live semantics: `detect(match, until)` only sees events <= until. Rolling rules are evaluated
at every completed minute boundary `cut <= until`; a moment's `detected_at` is the first cut at
which its rule held. After-windows are truncated at `until` and flagged incomplete.

Rules (thresholds in TH):
- sub_shift            substitution, then within 4-10' the team's progressive-action share in one
                       channel (L/C/R) rises >= 0.30 to >= 55% vs the 10' before (>= 6 progressive actions
                       after). Reported windows then grow with `until` up to 10' after the sub.
- red_card             every red card (before/after windows attached as they become available)
- shot_surge           team shots in last 10' >= 5 and >= previous 10' + 4
- momentum_swing       mean momentum of last 5' vs previous 5' moves >= 55 points towards a team
                       and the new mean is >= 30 in that team's favour
- channel_dominance    >= 8 final-third entries in last 10' with one channel >= 60% (previous 10' < 40%)
- possession_swing     pass share change >= 0.20 between consecutive 10' windows (>= 35 passes each)
- dangerous_sequences  >= 5 sequences reaching the box / ending in a shot in last 8', previous 8' <= 1
- goal                 every goal (context marker; not a "turning point" on its own)
Suppression: one moment per (type, team) within 15 minutes; rolling-rule moments of the same team
detected within 10 minutes of an earlier moment are merged into it (listed as supporting rules).
"""
from __future__ import annotations

from bisect import bisect_left

from .data import events_until
from .schemas import Event, Evidence, Match, MatchMoment, WindowMetrics
from .state import clock_label, momentum_series
from .windows import channel, is_progressive, window_metrics

TH = {
    "sub_min_after": 240, "sub_max_after": 600, "sub_share_delta": 0.3, "sub_min_prog": 6, "sub_after_share": 0.55,
    "shot_surge_min": 5, "shot_surge_gain": 4,
    "momentum_delta": 55.0, "momentum_level": 30.0,
    "channel_min_entries": 8, "channel_share": 0.6, "channel_prev_share": 0.4,
    "possession_delta": 0.2, "possession_min_passes": 35,
    "danger_min": 5, "danger_prev_max": 1, "danger_window": 480,
    "nms": 900, "cluster": 600,
}
CH_NAME = {"L": "left", "C": "centre", "R": "right"}
ROLLING = {"shot_surge", "momentum_swing", "channel_dominance", "possession_swing", "dangerous_sequences"}
SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}
RULES = {
    "sub_shift": "Substitution followed (4-10') by a >= 30-point rise (to >= 55%) in one channel's share of the team's progressive actions.",
    "red_card": "Every red card in the event stream.",
    "shot_surge": "Team shots in the last 10' >= 5 and at least 4 more than the previous 10'.",
    "momentum_swing": "Mean Rely momentum (last 5' vs previous 5') moves >= 55 points towards a team, new mean >= 30.",
    "channel_dominance": ">= 8 final-third entries in 10' with >= 60% through one channel (previous 10' < 40%).",
    "possession_swing": "Pass share changes >= 20 points between consecutive 10' windows (>= 35 passes each).",
    "dangerous_sequences": ">= 5 sequences reaching the box or ending in a shot in 8' after <= 1 in the previous 8'.",
    "goal": "Every goal in the event stream.",
}


def _pct(v: float) -> int:
    return int(round(v * 100))


def _confidence(effect: float, threshold: float, n: int, min_n: int, complete: bool) -> float:
    c = 0.5 + 0.25 * max(0.0, min(1.0, effect / threshold - 1.0)) + 0.2 * max(0.0, min(1.0, n / (2 * min_n)))
    if not complete:
        c -= 0.1
    return round(max(0.3, min(0.95, c)), 2)


def _metric_ev(mid: str, key: str, label: str, value, w: WindowMetrics | None, which: str, unit: str | None = None) -> Evidence:
    return Evidence(id=f"{mid}:{which}:{key}", kind="metric", label=label, value=value, unit=unit,
                    metric_path=f"moment.{which}.{key}", window=(w.start, w.end) if w else None)


def _window_ev(mid: str, before: WindowMetrics, after: WindowMetrics, complete: bool) -> Evidence:
    return Evidence(id=f"{mid}:windows", kind="window",
                    label=f"Before {clock_label(before.start)}-{clock_label(before.end)} vs after {clock_label(after.start)}-{clock_label(after.end)}"
                          + ("" if complete else " (after window still open)"),
                    window=(before.start, after.end))


class Detector:
    def __init__(self, match: Match, until: int):
        self.m = match
        self.until = until
        self.evs: list[Event] = events_until(match, until)
        self.names = match.player_names()
        self.out: list[MatchMoment] = []
        self.secs = [e.match_second for e in self.evs]
        self._wcache: dict[tuple[str, int, int], WindowMetrics] = {}

    def w(self, tid: str, start: int, end: int) -> WindowMetrics:
        key = (tid, start, end)
        if key not in self._wcache:
            lo, hi = bisect_left(self.secs, start), bisect_left(self.secs, end)
            self._wcache[key] = window_metrics(self.evs[lo:hi], tid, max(0, start), end)
        return self._wcache[key].model_copy(deep=True)

    def ba(self, tid: str, pivot: int, width: int = 600) -> tuple[WindowMetrics, WindowMetrics, bool]:
        before = self.w(tid, max(0, pivot - width), pivot)
        after = self.w(tid, pivot, min(pivot + width, self.until + 1))
        return before, after, self.until + 1 >= pivot + width

    def team_name(self, tid: str) -> str:
        return self.m.team(tid).name

    def add(self, mm: MatchMoment) -> None:
        for o in self.out:
            if mm.type in ("goal", "red_card"):
                break
            if o.type == mm.type and o.team_id == mm.team_id and abs(o.timestamp - mm.timestamp) < TH["nms"]:
                return
        self.out.append(mm)

    def cuts(self, start: int = 600):
        c = start
        while c <= self.until:
            yield c
            c += 60

    # ------------------------------------------------------------- rules
    def goals(self) -> None:
        for e in self.evs:
            if e.event_type != "Goal":
                continue
            mid = f"goal-{e.team_id}-{e.match_second}"
            scorer = self.names.get(e.player_id or "", "")
            shot_id = e.qualifiers.get("shot_event_id")
            seq_ids = [x.event_id for x in self.evs if x.sequence_id == e.sequence_id][-10:]
            self.add(MatchMoment(
                id=mid, timestamp=e.match_second, minute=e.minute, detected_at=e.match_second, type="goal",
                team_id=e.team_id, severity="medium", title=f"Goal - {scorer} ({self.team_name(e.team_id)})",
                title_key="tp.goal.title", params={"team": self.team_name(e.team_id), "player": scorer, "minute": e.minute},
                trigger={"event_id": e.event_id, "event_type": "Goal", "player_id": e.player_id, "description": "Goal scored"},
                evidence=[Evidence(id=f"{mid}:event", kind="event", label=f"Goal by {scorer} at {clock_label(e.match_second)}",
                                   event_ids=[e.event_id] + ([shot_id] if shot_id else []), timestamp=e.match_second),
                          Evidence(id=f"{mid}:seq", kind="sequence", label="Build-up sequence", event_ids=seq_ids,
                                   timestamp=e.match_second)],
                confidence=1.0, linked_event_ids=seq_ids, rule=RULES["goal"]))

    def red_cards(self) -> None:
        for e in self.evs:
            if not (e.event_type == "Card" and e.outcome == "Red"):
                continue
            opp = self.m.opponent(e.team_id)
            mid = f"red_card-{e.team_id}-{e.match_second}"
            b, a, complete = self.ba(opp, e.match_second)
            bt, at, _ = self.ba(e.team_id, e.match_second)
            player = self.names.get(e.player_id or "", "")
            ev = [
                Evidence(id=f"{mid}:event", kind="event", label=f"Red card: {player} ({self.team_name(e.team_id)})",
                         event_ids=[e.event_id], timestamp=e.match_second),
                _window_ev(mid, b, a, complete),
                _metric_ev(mid, "pass_share", f"{self.team_name(opp)} pass share before", _pct(b.pass_share), b, "before", "%"),
                _metric_ev(mid, "pass_share", f"{self.team_name(opp)} pass share after", _pct(a.pass_share), a, "after", "%"),
                _metric_ev(mid, "final_third_entries", f"{self.team_name(opp)} final-third entries before", b.final_third_entries, b, "before"),
                _metric_ev(mid, "final_third_entries", f"{self.team_name(opp)} final-third entries after", a.final_third_entries, a, "after"),
                Evidence(id=f"{mid}:team:high_pressures", kind="metric",
                         label=f"{self.team_name(e.team_id)} high pressures before/after", value=f"{bt.high_pressures}/{at.high_pressures}",
                         metric_path="moment.team.high_pressures"),
            ]
            self.add(MatchMoment(
                id=mid, timestamp=e.match_second, minute=e.minute, detected_at=e.match_second, type="red_card",
                team_id=e.team_id, severity="high",
                title=f"Red card reshapes the game - {self.team_name(e.team_id)} down to ten",
                title_key="tp.red_card.title", params={"team": self.team_name(e.team_id), "opponent": self.team_name(opp),
                                                       "player": player, "minute": e.minute,
                                                       "share_before": _pct(b.pass_share), "share_after": _pct(a.pass_share),
                                                       "territory_before": _pct(b.final_third_share), "territory_after": _pct(a.final_third_share),
                                                       "entries_before": b.final_third_entries, "entries_after": a.final_third_entries,
                                                       "press_before": bt.high_pressures, "press_after": at.high_pressures},
                trigger={"event_id": e.event_id, "event_type": "Card", "player_id": e.player_id, "description": "Red card"},
                before_state=b, after_state=a, after_window_complete=complete, evidence=ev,
                confidence=0.9 if complete else 0.75, linked_event_ids=[e.event_id] + a.event_ids[:12], rule=RULES["red_card"]))

    def sub_shifts(self) -> None:
        for e in self.evs:
            if e.event_type != "Substitution":
                continue
            ts, tid = e.match_second, e.team_id
            for cut in self.cuts(ts + TH["sub_min_after"]):
                if cut > ts + TH["sub_max_after"]:
                    break
                b = self.w(tid, max(0, ts - 600), ts)
                a = self.w(tid, ts, cut)
                if a.progressive_actions < TH["sub_min_prog"]:
                    continue
                best = max("LCR", key=lambda c: a.prog_share(c) - b.prog_share(c))
                delta = a.prog_share(best) - b.prog_share(best)
                if delta < TH["sub_share_delta"] or a.prog_share(best) < TH["sub_after_share"]:
                    continue
                # Report windows as of `until` (after window grows to 10', never past `until`).
                b, a, complete = self.ba(tid, ts)
                delta = a.prog_share(best) - b.prog_share(best)
                faded = delta < TH["sub_share_delta"] * 0.5
                mid = f"sub_shift-{tid}-{ts}"
                p_in = e.qualifiers.get("player_in")
                ch_events = [x.event_id for x in self.evs if x.team_id == tid and a.start <= x.match_second < a.end
                             and is_progressive(x) and channel(x.end_y or 50) == best]
                shots_after = [x.event_id for x in self.evs if x.team_id == tid and x.event_type == "Shot" and a.start <= x.match_second < a.end]
                key_player = self._key_player(tid, a.start, a.end, best)
                ev = [
                    Evidence(id=f"{mid}:event", kind="event",
                             label=f"Substitution {clock_label(ts)}: {self.names.get(p_in, p_in)} on for {self.names.get(e.player_id or '', '')}",
                             event_ids=[e.event_id], timestamp=ts),
                    _window_ev(mid, b, a, complete),
                    _metric_ev(mid, f"prog_share_{best}", f"{CH_NAME[best].title()}-channel share of progressive actions before", _pct(b.prog_share(best)), b, "before", "%"),
                    _metric_ev(mid, f"prog_share_{best}", f"{CH_NAME[best].title()}-channel share of progressive actions after", _pct(a.prog_share(best)), a, "after", "%"),
                    _metric_ev(mid, f"prog_{best}", f"{CH_NAME[best].title()}-channel progressive actions after", getattr(a, f"prog_{best}"), a, "after"),
                    _metric_ev(mid, "progressive_actions", "Progressive actions after", a.progressive_actions, a, "after"),
                    _metric_ev(mid, "shots", "Shots before", b.shots, b, "before"),
                    _metric_ev(mid, "shots", "Shots after", a.shots, a, "after"),
                    _metric_ev(mid, "box_entries", "Box entries after", a.box_entries, a, "after"),
                    Evidence(id=f"{mid}:seq", kind="sequence", label=f"{CH_NAME[best].title()}-channel progressive actions after the change",
                             event_ids=ch_events[:15], timestamp=ts),
                ]
                if key_player:
                    ev.append(Evidence(id=f"{mid}:player", kind="metric", label=f"Most involved in the {CH_NAME[best]} channel: {self.names[key_player[0]]}",
                                       value=key_player[1], metric_path=f"moment.player.{key_player[0]}"))
                self.add(MatchMoment(
                    id=mid, timestamp=ts, minute=e.minute, detected_at=cut, type="sub_shift", team_id=tid,
                    severity="low" if faded else ("high" if delta >= 0.3 or a.shots >= b.shots + 3 else "medium"),
                    title=f"{self.team_name(tid)}'s {e.minute}' change moves the attack to the {CH_NAME[best]}",
                    title_key="tp.sub_shift.title",
                    params={"team": self.team_name(tid), "minute": e.minute, "channel": best,
                            "player_in": self.names.get(p_in, p_in), "player_out": self.names.get(e.player_id or "", ""),
                            "share_before": _pct(b.prog_share(best)), "share_after": _pct(a.prog_share(best)),
                            "prog_after": getattr(a, f"prog_{best}"), "shots_before": b.shots, "shots_after": a.shots,
                            "box_after": a.box_entries,
                            "key_player": self.names[key_player[0]] if key_player else None,
                            "key_player_actions": key_player[1] if key_player else None,
                            "note": e.qualifiers.get("note", ""), "faded": faded},
                    trigger={"event_id": e.event_id, "event_type": "Substitution", "player_id": e.player_id,
                             "player_in": p_in, "description": "Substitution"},
                    before_state=b, after_state=a, after_window_complete=complete, evidence=ev,
                    confidence=round(max(0.3, _confidence(max(delta, 0.0), TH["sub_share_delta"], a.progressive_actions, TH["sub_min_prog"], complete) - (0.2 if faded else 0.0)), 2),
                    linked_event_ids=[e.event_id] + ch_events[:12] + shots_after[:5], rule=RULES["sub_shift"]))
                break

    def _key_player(self, tid: str, start: int, end: int, ch: str) -> tuple[str, int] | None:
        cnt: dict[str, int] = {}
        for x in self.evs:
            if x.team_id == tid and start <= x.match_second < end and x.player_id and is_progressive(x) and channel(x.end_y or 50) == ch:
                cnt[x.player_id] = cnt.get(x.player_id, 0) + 1
        if not cnt:
            return None
        pid = max(sorted(cnt), key=lambda p: cnt[p])
        return pid, cnt[pid]

    def rolling(self) -> None:
        home, away = self.m.home_team_id, self.m.away_team_id
        series = momentum_series(self.evs, home, away, self.until)
        for cut in self.cuts(600):
            for tid in (home, away):
                prev = self.w(tid, cut - 1200, cut - 600) if cut >= 1200 else None
                cur = self.w(tid, cut - 600, cut)
                # shot surge
                if prev is not None and cur.shots >= TH["shot_surge_min"] and cur.shots >= prev.shots + TH["shot_surge_gain"]:
                    self._window_moment("shot_surge", tid, cut, prev, cur, "shots", cur.shots - prev.shots, TH["shot_surge_gain"],
                                        f"{self.team_name(tid)} shot surge", {"shots_before": prev.shots, "shots_after": cur.shots,
                                                                             "xg_after": cur.xg})
                # channel dominance
                if cur.final_third_entries >= TH["channel_min_entries"] and prev is not None:
                    ch = max("LCR", key=cur.share)
                    if cur.share(ch) >= TH["channel_share"] and prev.share(ch) < TH["channel_prev_share"]:
                        self._window_moment("channel_dominance", tid, cut, prev, cur, f"entries_{ch}", cur.share(ch) - prev.share(ch), 0.15,
                                            f"{self.team_name(tid)} dominate the {CH_NAME[ch]} channel",
                                            {"channel": ch, "share_before": _pct(prev.share(ch)), "share_after": _pct(cur.share(ch)),
                                             "entries_after": cur.final_third_entries, "channel_entries": getattr(cur, f"entries_{ch}")})
                # possession swing
                if prev is not None and prev.passes >= TH["possession_min_passes"] and cur.passes >= TH["possession_min_passes"]:
                    d = cur.pass_share - prev.pass_share
                    if d >= TH["possession_delta"]:
                        self._window_moment("possession_swing", tid, cut, prev, cur, "pass_share", d, TH["possession_delta"],
                                            f"{self.team_name(tid)} take control of the ball",
                                            {"share_before": _pct(prev.pass_share), "share_after": _pct(cur.pass_share)})
                # dangerous sequences
                W = TH["danger_window"]
                if cut >= 2 * W:
                    dp = self.w(tid, cut - 2 * W, cut - W)
                    dc = self.w(tid, cut - W, cut)
                    if dc.dangerous_sequences >= TH["danger_min"] and dp.dangerous_sequences <= TH["danger_prev_max"]:
                        self._window_moment("dangerous_sequences", tid, cut, dp, dc, "dangerous_sequences",
                                            dc.dangerous_sequences - dp.dangerous_sequences, 2,
                                            f"{self.team_name(tid)} keep arriving in the box",
                                            {"seq_before": dp.dangerous_sequences, "seq_after": dc.dangerous_sequences,
                                             "box_after": dc.box_entries})
            # momentum swing
            m = cut // 60
            if m >= 10 and m < len(series):
                now = sum(series[m - 4:m + 1]) / 5
                before = sum(series[m - 9:m - 4]) / 5
                d = now - before
                for tid, sign in ((home, 1), (away, -1)):
                    if sign * d >= TH["momentum_delta"] and sign * now >= TH["momentum_level"]:
                        prev = self.w(tid, cut - 600, cut - 300)
                        cur = self.w(tid, cut - 300, cut)
                        self._window_moment("momentum_swing", tid, cut, prev, cur, "momentum", abs(d), TH["momentum_delta"],
                                            f"Momentum swings to {self.team_name(tid)}",
                                            {"momentum_before": round(sign * before), "momentum_after": round(sign * now),
                                             "high_press_after": cur.high_pressures, "recoveries_after": cur.recoveries,
                                             "entries_after": cur.final_third_entries, "shots_after": cur.shots},
                                            extra_ev=[Evidence(id=f"momentum_swing-{tid}-{cut}:momentum", kind="metric",
                                                               label="Mean momentum (team-positive) previous 5' -> last 5'",
                                                               value=f"{round(sign * before)} -> {round(sign * now)}",
                                                               metric_path="state.momentum_series")])

    def _window_moment(self, typ: str, tid: str, cut: int, prev: WindowMetrics, cur: WindowMetrics, key: str,
                       effect: float, threshold: float, title: str, params: dict, extra_ev: list[Evidence] | None = None) -> None:
        mid = f"{typ}-{tid}-{cut}"
        ev = [_window_ev(mid, prev, cur, True)]
        for k, lbl in (("shots", "Shots"), ("final_third_entries", "Final-third entries"), ("box_entries", "Box entries"),
                       ("high_pressures", "High pressures"), ("recoveries", "Recoveries"), ("dangerous_sequences", "Dangerous sequences")):
            ev.append(_metric_ev(mid, k, f"{lbl} before", getattr(prev, k), prev, "before"))
            ev.append(_metric_ev(mid, k, f"{lbl} after", getattr(cur, k), cur, "after"))
        if key == "pass_share":
            ev.append(_metric_ev(mid, "pass_share", "Pass share before", _pct(prev.pass_share), prev, "before", "%"))
            ev.append(_metric_ev(mid, "pass_share", "Pass share after", _pct(cur.pass_share), cur, "after", "%"))
        if extra_ev:
            ev.extend(extra_ev)
        shots = [x.event_id for x in self.evs if x.team_id == tid and x.event_type == "Shot" and cur.start <= x.match_second < cur.end]
        ev.append(Evidence(id=f"{mid}:events", kind="sequence", label="Key events in the window",
                           event_ids=(shots + cur.event_ids)[:15], timestamp=cur.start))
        n = cur.final_third_entries + cur.shots + cur.passes // 10
        params = {"team": self.team_name(tid), "minute": cut // 60, **params}
        self.add(MatchMoment(
            id=mid, timestamp=cut, minute=cut // 60, detected_at=cut, type=typ, team_id=tid,  # type: ignore[arg-type]
            severity="high" if effect >= 2 * threshold else "medium", title=title, title_key=f"tp.{typ}.title", params=params,
            trigger={"event_id": None, "event_type": "window", "description": RULES[typ], "window": [cur.start, cur.end]},
            before_state=prev, after_state=cur, after_window_complete=True, evidence=ev,
            confidence=_confidence(effect, threshold, n, 8, True), linked_event_ids=(shots + cur.event_ids)[:20], rule=RULES[typ]))

    def run(self) -> list[MatchMoment]:
        self.goals()
        self.red_cards()
        self.sub_shifts()
        self.rolling()
        return self._cluster(sorted(self.out, key=lambda x: (x.detected_at, x.id)))

    @staticmethod
    def _cluster(moments: list[MatchMoment]) -> list[MatchMoment]:
        kept: list[MatchMoment] = []
        for mm in moments:
            if mm.type in ROLLING:
                host = next((k for k in reversed(kept) if k.type != "goal" and k.team_id == mm.team_id
                             and 0 <= mm.detected_at - k.detected_at <= TH["cluster"]), None)
                if host is not None:
                    host.params.setdefault("supporting_rules", []).append(mm.type)
                    host.evidence.append(Evidence(id=f"{mm.id}:support", kind="rule",
                                                  label=f"Also triggered: {mm.type.replace('_', ' ')} at {clock_label(mm.detected_at)}",
                                                  timestamp=mm.detected_at))
                    continue
            kept.append(mm)
        return kept


_CACHE: dict[tuple[str, int], list[MatchMoment]] = {}


def detect(match: Match, until: int) -> list[MatchMoment]:
    until = max(0, min(until, match.duration_seconds))
    key = (match.match_id, until)
    if key not in _CACHE:
        if len(_CACHE) > 4000:
            _CACHE.clear()
        _CACHE[key] = Detector(match, until).run()
    return [m.model_copy(deep=True) for m in _CACHE[key]]


def headline_moment(moments: list[MatchMoment]) -> MatchMoment | None:
    """The turning point to feature: highest severity, then confidence, earliest; goals excluded."""
    cands = [m for m in moments if m.type != "goal"]
    if not cands:
        return None
    pri = {"sub_shift": 3, "red_card": 3, "momentum_swing": 2, "dangerous_sequences": 2, "shot_surge": 2,
           "channel_dominance": 1, "possession_swing": 1}
    return sorted(cands, key=lambda m: (-pri.get(m.type, 0), -SEVERITY_ORDER[m.severity], -m.confidence, m.detected_at))[0]
