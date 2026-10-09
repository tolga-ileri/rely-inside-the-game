"""Deterministic seed selection: scan seeds from each scenario's `base_seed` upwards and keep the
first one whose generated match satisfies the scenario's acceptance criteria (story beats +
realism bounds). The chosen seed is written back to scenarios/<name>.json, so generation itself
remains a pure function of the scenario file.

Usage (needs the API package for the detector):
    apps/api/.venv/Scripts/python synthetic-data/generators/select_seeds.py [scenario ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[0] / "apps" / "api"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate import Gen  # noqa: E402

from rely_brain.schemas import Match  # noqa: E402
from rely_brain.state import compute_state  # noqa: E402
from rely_brain.turning_points import detect, headline_moment  # noqa: E402


def realistic(m: Match) -> bool:
    st = compute_state(m, m.duration_seconds)
    return all(8 <= t.shots <= 22 for t in st.teams.values()) and all(t.xg <= 3.6 for t in st.teams.values())


def goals_ok(sc: dict, m: Match) -> bool:
    tid = {"home": m.home_team_id, "away": m.away_team_id}
    want = sorted((g["minute"], tid[g["team"]]) for g in sc["goals"])
    got = sorted((e.minute, e.team_id) for e in m.events if e.event_type == "Goal")
    return len(got) == len(want) and all(w[1] == g[1] and 0 <= g[0] - w[0] <= 7 for w, g in zip(want, got, strict=True))


def accept(name: str, sc: dict, m: Match) -> bool:
    if not (goals_ok(sc, m) and realistic(m)):
        return False
    full = detect(m, m.duration_seconds)
    head = headline_moment(full)
    if name == "tactical_shift":
        if not head or head.type != "sub_shift" or head.team_id != m.home_team_id or head.params.get("channel") != "R":
            return False
        if not (3600 <= head.detected_at <= 3700):
            return False
        p = head.params
        live = next(x for x in detect(m, head.detected_at + 60) if x.id == head.id).params
        return (p["share_after"] - p["share_before"] >= 30 and live["share_after"] - live["share_before"] >= 30
                and p["shots_after"] > p["shots_before"] and not p["faded"])
    if name == "red_card":
        if not head or head.type != "red_card":
            return False
        p = head.params
        return p["share_after"] >= p["share_before"] + 15 and p["territory_after"] >= p["territory_before"] + 15 and p["press_after"] < p["press_before"]
    if name == "late_comeback":
        first_goal = min(e.match_second for e in m.events if e.event_type == "Goal" and e.team_id == m.home_team_id)
        rolling = {"momentum_swing", "shot_surge", "dangerous_sequences"}
        early = [x for x in full if x.team_id == m.home_team_id and 4200 <= x.detected_at < first_goal
                 and not x.params.get("faded")
                 and (x.type in rolling or rolling & set(x.params.get("supporting_rules", [])))]
        return bool(early) and head is not None and head.team_id == m.home_team_id and head.detected_at < first_goal
    return head is not None


def main(names: list[str]) -> None:
    teams = json.loads((ROOT / "scenarios" / "teams.json").read_text(encoding="utf-8"))
    names = names or sorted(p.stem for p in (ROOT / "scenarios").glob("*.json") if p.stem != "teams")
    for name in names:
        path = ROOT / "scenarios" / f"{name}.json"
        sc = json.loads(path.read_text(encoding="utf-8"))
        for seed in range(sc["base_seed"], sc["base_seed"] + 400):
            sc["seed"] = seed
            m = Match.model_validate(Gen(sc, teams).run())
            if accept(name, sc, m):
                print(f"{name}: seed {seed} accepted")
                path.write_text(json.dumps(sc, indent=1), encoding="utf-8")
                break
        else:
            print(f"{name}: no seed accepted in range")


if __name__ == "__main__":
    main(sys.argv[1:])
