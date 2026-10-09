"""Seeded, deterministic synthetic football event generator for Rely Match Brain.

All data is SYNTHETIC: fictional clubs, fictional players, simulated events.
Coordinates are 0-100 in the acting team's attacking frame (x=100 is the goal the
acting team attacks; y<33.3 left channel, 33.3-66.7 centre, >66.7 right channel).

Usage:  python synthetic-data/generators/generate.py            # all scenarios
        python synthetic-data/generators/generate.py tactical_shift
Only the Python standard library is used, so output is identical everywhere.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_VERSION = "1.0.0"
HALF = 2700
FULL = 5400

ZONES = {  # role: (x_min, x_max, channels)
    "GK": (0, 18, "C"), "CB": (0, 45, "C"), "RB": (15, 75, "R"), "LB": (15, 75, "L"),
    "IRB": (35, 72, "CR"), "DM": (25, 60, "C"), "CM": (35, 80, "LCR"), "RW": (55, 100, "R"),
    "LW": (55, 100, "L"), "ST": (65, 100, "C"),
}
CENTRE = {"L": 17.0, "C": 50.0, "R": 83.0}


def channel_of(y: float) -> str:
    return "L" if y < 33.34 else ("R" if y > 66.66 else "C")


def clamp(v: float, lo: float = 0.5, hi: float = 99.5) -> float:
    return round(max(lo, min(hi, v)), 1)


class Gen:
    def __init__(self, sc: dict, teams: dict):
        self.sc = sc
        self.rng = random.Random(sc["seed"])
        self.match_id = sc["match_id"]
        self.sides = {"home": teams[sc["home"]], "away": teams[sc["away"]]}
        self.tid = {s: self.sides[s]["team_id"] for s in self.sides}
        self.side_of = {v: k for k, v in self.tid.items()}
        self.roles: dict[str, str] = {}
        self.active: dict[str, list[str]] = {}
        for s, team in self.sides.items():
            plist = team["players"]
            self.active[s] = [p[0] for p in plist[:11]]
            for p in plist:
                self.roles[p[0]] = p[3]
        self.events: list[dict] = []
        self.t = 0
        self.pid = 0
        self.seq = 0
        self.period = 1
        self.goals = [dict(g, done=False) for g in sc.get("goals", [])]
        self.sched = sorted(
            [("sub", s["minute"] * 60, s) for s in sc.get("subs", [])]
            + [("red", r["minute"] * 60, r) for r in sc.get("red_cards", [])]
            + [("role", r["minute"] * 60, r) for r in sc.get("role_changes", [])],
            key=lambda e: e[1],
        )

    # ---------- helpers
    def params(self, side: str) -> dict:
        minute = self.t // 60
        cur = self.sc["phases"][0][side]
        for ph in self.sc["phases"]:
            if minute >= ph["from"]:
                cur = ph[side]
        return cur

    def opp(self, side: str) -> str:
        return "away" if side == "home" else "home"

    def pick(self, side: str, x: float, y: float, exclude: str | None = None,
             roles: tuple[str, ...] | None = None) -> str:
        ch = channel_of(y)
        cands, weights = [], []
        for pid in self.active[side]:
            if pid == exclude:
                continue
            role = self.roles[pid]
            if roles and role not in roles:
                continue
            if role == "GK" and x > 20:
                continue
            x0, x1, chs = ZONES[role]
            w = 0.15
            if x0 <= x <= x1:
                w += 1.2
            if ch in chs:
                w += 1.0
            if x0 <= x <= x1 and ch in chs:
                w += 2.0
            cands.append(pid)
            weights.append(w)
        if not cands:
            cands = [p for p in self.active[side] if p != exclude] or self.active[side]
            weights = [1.0] * len(cands)
        return self.rng.choices(cands, weights)[0]

    def emit(self, etype: str, side: str, player: str | None, x: float, y: float, ex=None, ey=None,
             outcome: str | None = None, q: dict | None = None) -> dict:
        ms = int(self.t)
        ev = {
            "event_id": f"{self.match_id}-{len(self.events) + 1:05d}",
            "match_id": self.match_id,
            "period": self.period,
            "match_second": ms,
            "minute": ms // 60,
            "second": ms % 60,
            "team_id": self.tid[side],
            "player_id": player,
            "event_type": etype,
            "outcome": outcome,
            "start_x": clamp(x), "start_y": clamp(y),
            "end_x": None if ex is None else clamp(ex), "end_y": None if ey is None else clamp(ey),
            "possession_id": self.pid,
            "sequence_id": self.seq,
            "qualifiers": q or {},
            "metadata": {"synthetic": True},
        }
        self.events.append(ev)
        return ev

    def tick(self, side: str, lo: float = 0.6, hi: float = 1.5) -> None:
        tempo = self.params(side)["tempo"]
        self.t += max(1, round(tempo * self.rng.uniform(lo, hi)))

    def period_over(self) -> bool:
        return self.t >= (HALF if self.period == 1 else FULL)

    def process_schedule(self) -> None:
        while self.sched and self.sched[0][1] <= self.t:
            kind, _, item = self.sched.pop(0)
            if kind == "role":
                self.roles[item["player"]] = item["role"]
                continue
            side = item["team"]
            if kind == "sub":
                off, on = item["off"], item["on"]
                if off in self.active[side]:
                    self.active[side][self.active[side].index(off)] = on
                    self.emit("Substitution", side, off, 50, 0.5,
                              q={"player_in": on, "player_out": off, "note": item.get("note", "")})
            elif kind == "red":
                pl = item["player"]
                self.emit("Foul", side, pl, 45, 50, outcome="Committed", q={"severity": "serious"})
                self.emit("Card", side, pl, 45, 50, outcome="Red", q={"card": "red"})
                if pl in self.active[side]:
                    self.active[side].remove(pl)

    def pending_goal(self, side: str):
        for g in self.goals:
            limit = min(420, FULL - 20 - g["minute"] * 60)
            if not g["done"] and g["team"] == side and g["minute"] * 60 <= self.t < g["minute"] * 60 + limit:
                return g
        return None

    # ---------- possession
    def possession(self, side: str, x: float, y: float, start: str):
        """Play one possession; returns (next_side, x, y, how) in the next side's frame."""
        rng = self.rng
        self.pid += 1
        self.seq += 1
        p = self.params(side)
        o = self.opp(side)
        po = self.params(o)
        goal = self.pending_goal(side)
        if goal:
            goal["done"] = True
        target = rng.choices(["L", "C", "R"], p["ch"])[0]
        ty = CENTRE[target]
        player = self.pick(side, x, y)
        if start == "recovery":
            self.emit("Ball Recovery", side, player, x, y, outcome="Won")
        elif start in ("kick_off", "goal_kick", "throw_in", "free_kick", "corner"):
            self.emit("Restart", side, player, x, y, q={"restart": start})
        while True:
            self.process_schedule()
            if self.period_over():
                return o, 50, 50, "period_end"
            pressured = False
            press_p = po["press"] * (0.45 + po["high"] * x / 100.0)
            if rng.random() < press_p:
                pr = self.pick(o, 100 - x, 100 - y)
                self.emit("Pressure", o, pr, 100 - x, 100 - y, q={"on_player": player})
                pressured = True
            loss_p = 0.075 + (0.5 - p["poss"]) * 0.5 + (0.09 if pressured else 0) + x / 100 * 0.07
            if x >= 78:
                loss_p += 0.22  # crowded box / last third
            if goal:
                loss_p = 0.0
            if not goal and rng.random() < 0.025:  # foul won
                fo = self.pick(o, 100 - x, 100 - y)
                self.emit("Foul", o, fo, 100 - x, 100 - y, outcome="Committed")
                if rng.random() < 0.14:
                    self.emit("Card", o, fo, 100 - x, 100 - y, outcome="Yellow", q={"card": "yellow"})
                self.tick(side, 2, 5)
                self.seq += 1
                self.emit("Restart", side, player, x, y, q={"restart": "free_kick"})
                continue
            if x >= 80 and 25 <= y <= 75 and (goal or rng.random() < p["shot"]):
                return self.shot(side, player, x, y, goal)
            if x >= 72 and channel_of(y) != "C" and rng.random() < (0.9 if goal else 0.35):
                ex, ey = rng.uniform(86, 95), rng.uniform(38, 62)
                ok = goal is not None or rng.random() < 0.22
                self.emit("Cross", side, player, x, y, ex, ey, outcome="Complete" if ok else "Incomplete")
                self.tick(side)
                if ok:
                    receiver = self.pick(side, ex, ey, exclude=player, roles=("ST", "RW", "LW", "CM", "IRB"))
                    return self.shot(side, receiver, ex, ey, goal, header=True)
                cl = self.pick(o, 100 - ex, 100 - ey, roles=("CB", "RB", "LB", "DM", "GK"))
                self.emit("Clearance", o, cl, 100 - ex, 100 - ey, rng.uniform(25, 55), rng.uniform(10, 90),
                          outcome="Success")
                self.tick(side)
                if rng.random() < 0.45:
                    nx, ny = rng.uniform(55, 72), rng.uniform(15, 85)
                    self.emit("Ball Recovery", side, self.pick(side, nx, ny), nx, ny, outcome="Won",
                              q={"second_ball": True})
                    x, y = nx, ny
                    self.seq += 1
                    continue
                nx, ny = rng.uniform(25, 50), rng.uniform(15, 85)
                self.emit("Possession Change", o, None, nx, ny)
                return o, nx, ny, "recovery"
            if rng.random() < 0.26:  # carry / dribble
                adv = max(-3.0, rng.gauss(p["prog"] * 0.55, 5))
                ex, ey = x + adv, y + (ty - y) * rng.uniform(0.2, 0.6) + rng.gauss(0, 5)
                if pressured and rng.random() < 0.45:
                    ok = goal is not None or rng.random() > 0.42
                    self.emit("Dribble", side, player, x, y, ex, ey, outcome="Complete" if ok else "Incomplete")
                    o_player = self.pick(o, 100 - x, 100 - y)
                    self.emit("Duel", o, o_player, 100 - x, 100 - y, outcome="Lost" if ok else "Won")
                    if not ok:
                        self.tick(side)
                        self.emit("Tackle", o, o_player, 100 - x, 100 - y, outcome="Won")
                        self.emit("Possession Change", o, o_player, 100 - x, 100 - y)
                        return o, 100 - x, 100 - y, "recovery_live"
                else:
                    self.emit("Carry", side, player, x, y, ex, ey, outcome="Complete")
                x, y = clamp(ex), clamp(ey)
                self.tick(side, 0.5, 1.1)
                if not goal and rng.random() < loss_p * 0.6:
                    tk = self.pick(o, 100 - x, 100 - y)
                    self.emit("Tackle", o, tk, 100 - x, 100 - y, outcome="Won")
                    self.emit("Possession Change", o, tk, 100 - x, 100 - y)
                    return o, 100 - x, 100 - y, "recovery_live"
                continue
            if not goal and x < 45 and rng.random() < p.get("direct", 0.0):  # long ball out of a deep block
                ex, ey = clamp(x + rng.gauss(35, 8)), clamp(rng.uniform(20, 80))
                if rng.random() < 0.65:
                    self.emit("Pass", side, player, x, y, ex, ey, outcome="Incomplete", q={"long_ball": True})
                    self.tick(side, 0.5, 1.0)
                    win = self.pick(o, 100 - ex, 100 - ey)
                    self.emit("Duel", o, win, 100 - ex, 100 - ey, outcome="Won", q={"aerial": True})
                    self.emit("Possession Change", o, win, 100 - ex, 100 - ey)
                    return o, 100 - ex, 100 - ey, "recovery_live"
                receiver = self.pick(side, ex, ey, exclude=player)
                self.emit("Pass", side, player, x, y, ex, ey, outcome="Complete", q={"receiver": receiver, "long_ball": True})
                x, y, player = ex, ey, receiver
                self.tick(side)
                continue
            back = rng.random() < (0.22 if x < 70 else 0.3) and not goal
            adv = -abs(rng.gauss(8, 5)) if back else rng.gauss(p["prog"], 9)
            if goal:
                adv = abs(adv) + 6
            ex = clamp(x + adv)
            steer = (0.5, 0.95) if x > 30 else (0.2, 0.55)
            ey = clamp(y + (ty - y) * rng.uniform(*steer) + rng.gauss(0, 6))
            receiver = self.pick(side, ex, ey, exclude=player)
            if rng.random() < 0.025 and not goal:
                side_line = 99.5 if ey > 50 else 0.5
                self.emit("Pass", side, player, x, y, ex, side_line, outcome="Out")
                self.tick(side, 2, 4)
                self.emit("Possession Change", o, None, 100 - ex, 100 - side_line)
                return o, 100 - ex, 100 - side_line, "throw_in"
            if rng.random() < loss_p:
                self.emit("Pass", side, player, x, y, ex, ey, outcome="Incomplete", q={"intended": receiver})
                it = self.pick(o, 100 - ex, 100 - ey)
                self.tick(side, 0.3, 0.8)
                self.emit("Interception", o, it, 100 - ex, 100 - ey, outcome="Won")
                self.emit("Possession Change", o, it, 100 - ex, 100 - ey)
                return o, 100 - ex, 100 - ey, "recovery_live"
            self.emit("Pass", side, player, x, y, ex, ey, outcome="Complete", q={"receiver": receiver})
            x, y, player = ex, ey, receiver
            self.tick(side)

    def shot(self, side: str, player: str, x: float, y: float, goal, header: bool = False):
        rng = self.rng
        o = self.opp(side)
        dist = math.hypot((100 - x) * 1.05, (50 - y) * 0.68)
        xg = round(max(0.02, min(0.6, 0.6 * math.exp(-dist / 9.5) * (0.6 if header else 1.0))), 2)
        q = {"xg": xg, "body_part": "Head" if header else rng.choice(["Right Foot", "Left Foot", "Right Foot"])}
        self.tick(side, 0.3, 0.8)
        if goal:
            ev = self.emit("Shot", side, player, x, y, 100, rng.uniform(46, 54), outcome="Goal", q=q)
            self.emit("Goal", side, player, 100, ev["end_y"], outcome="Scored", q={"shot_event_id": ev["event_id"]})
            self.t += 50
            self.seq += 1
            return o, 50, 50, "kick_off"
        r = rng.random()
        if r < 0.36:
            self.emit("Shot", side, player, x, y, 100, rng.uniform(45, 55), outcome="Saved", q=q)
            gk = self.pick(o, 2, 50, roles=("GK",))
            self.emit("Goalkeeper Action", o, gk, 2, 50, outcome="Saved")
            self.tick(o, 1, 3)
            return o, 8, 50, "gk"
        if r < 0.70:
            ey = rng.choice([rng.uniform(30, 43), rng.uniform(57, 70)])
            self.emit("Shot", side, player, x, y, 100, ey, outcome="Off Target", q=q)
            self.t += rng.randint(15, 30)
            return o, 6, 50, "goal_kick"
        bl = self.pick(o, 100 - x, 100 - y, roles=("CB", "RB", "LB", "DM", "IRB"))
        self.emit("Shot", side, player, x, y, x + 3, y, outcome="Blocked", q=q)
        self.emit("Clearance", o, bl, 100 - x, 100 - y, rng.uniform(15, 40), rng.uniform(5, 95), outcome="Blocked shot")
        self.tick(side, 1, 2)
        if rng.random() < 0.45:
            self.t += rng.randint(10, 20)
            self.seq += 1
            cy = rng.choice([0.5, 99.5])
            taker = self.pick(side, 99, cy, roles=("RW", "LW", "CM"))
            self.emit("Restart", side, taker, 99.5, cy, q={"restart": "corner"})
            ex, ey = rng.uniform(86, 94), rng.uniform(38, 62)
            self.emit("Cross", side, taker, 99.5, cy, ex, ey, outcome="Incomplete", q={"from_corner": True})
            cl = self.pick(o, 100 - ex, 100 - ey, roles=("CB", "DM", "GK"))
            self.emit("Clearance", o, cl, 100 - ex, 100 - ey, rng.uniform(25, 50), rng.uniform(10, 90), outcome="Success")
            self.tick(o)
        nx, ny = rng.uniform(20, 40), rng.uniform(15, 85)
        self.emit("Possession Change", o, None, nx, ny)
        return o, nx, ny, "recovery"

    def run(self) -> dict:
        side, x, y, how = "home", 50.0, 50.0, "kick_off"
        while True:
            if self.period_over():
                if self.period == 1:
                    self.period = 2
                    self.t = max(HALF, self.t)  # first-half stoppage time never overlaps the second half
                    side, x, y, how = "away", 50.0, 50.0, "kick_off"
                    continue
                break
            if how == "recovery_live":
                how = "recovery"
            elif how == "gk":
                how = "goal_kick"
            elif how == "period_end":
                how = "kick_off"
            side, x, y, how = self.possession(side, x, y, how)
        teams = []
        for s in ("home", "away"):
            t = self.sides[s]
            teams.append({
                "side": s, "team_id": t["team_id"], "name": t["name"], "short": t["short"], "color": t["color"],
                "crest": t["crest"],
                "players": [{"player_id": p[0], "name": p[1], "number": p[2], "position": p[3], "starter": i < 11}
                            for i, p in enumerate(t["players"])],
            })
        counts: dict[str, int] = {}
        for e in self.events:
            counts[e["event_type"]] = counts.get(e["event_type"], 0) + 1
        return {
            "match_id": self.match_id, "scenario": self.sc["scenario"], "title": self.sc["title"],
            "synthetic": True,
            "data_statement": "Synthetic football-realistic data. Fictional clubs and players. Not real match data.",
            "generator": {"version": GENERATOR_VERSION, "seed": self.sc["seed"]},
            "duration_seconds": FULL, "demo": self.sc.get("demo", {}),
            "home_team_id": self.tid["home"], "away_team_id": self.tid["away"], "teams": teams,
            "event_count": len(self.events), "event_type_counts": dict(sorted(counts.items())),
            "events": self.events,
        }


def generate(name: str) -> dict:
    teams = json.loads((ROOT / "scenarios" / "teams.json").read_text(encoding="utf-8"))
    sc = json.loads((ROOT / "scenarios" / f"{name}.json").read_text(encoding="utf-8"))
    return Gen(sc, teams).run()


def main(argv: list[str]) -> None:
    names = argv or sorted(p.stem for p in (ROOT / "scenarios").glob("*.json") if p.stem != "teams")
    index = []
    for n in names:
        m = generate(n)
        out = ROOT / "matches" / f"{m['match_id']}.json"
        out.write_text(json.dumps(m, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
        goals = [(e["minute"], e["team_id"]) for e in m["events"] if e["event_type"] == "Goal"]
        index.append({"match_id": m["match_id"], "scenario": m["scenario"], "title": m["title"],
                      "event_count": m["event_count"], "goals": goals})
        print(f"{n:16s} {m['match_id']:28s} events={m['event_count']} goals={goals}")
    if not argv:
        (ROOT / "matches" / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
