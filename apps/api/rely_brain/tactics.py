"""Tactical Response + What-if. Structured shapes for the Studio-style pitch preview.

Coordinates: 0-100, x towards the opponent goal, y from the team's left (0) to right (100) touchline.
What-if never predicts a score; it states effect, advantage, risk, players and limitations.
"""
from __future__ import annotations

from typing import Any

from . import i18n
from .data import events_until
from .narrative import localise, moment_facts
from .schemas import Action, Match, MatchMoment, MetricRef, Scenario

SHAPES: dict[str, dict[str, tuple[float, float]]] = {
    "4-3-3": {"GK": (5, 50), "LB": (30, 14), "LCB": (22, 36), "RCB": (22, 64), "RB": (30, 86), "DM": (40, 50),
              "LCM": (54, 32), "RCM": (54, 68), "LW": (74, 12), "ST": (80, 50), "RW": (74, 88)},
    "3-2-5": {"GK": (5, 50), "LCB": (24, 26), "DM": (20, 50), "RCB": (24, 74), "RB": (44, 58), "LCM": (44, 40),
              "LB": (78, 8), "LW": (80, 32), "ST": (84, 50), "RCM": (78, 68), "RW": (80, 92)},
    "5-4-1": {"GK": (5, 50), "LW": (28, 8), "LCB": (20, 30), "DM": (18, 50), "RCB": (20, 70), "RB": (28, 92),
              "LB": (42, 18), "LCM": (42, 40), "RCM": (42, 60), "RW": (42, 82), "ST": (62, 50)},
}
PLAYBOOK_SHAPE = {"amplify_3_2_5": ("4-3-3", "3-2-5"), "hold_4_3_3": ("4-3-3", "4-3-3"), "counter_5_4_1": ("4-3-3", "5-4-1")}
MOVE_TEXT = {
    "amplify_3_2_5": {
        "RB": {"en": "inverts into midfield next to the holding midfielder", "tr": "içeri kat ederek ön liberonun yanına geçer", "es": "se mete por dentro junto al pivote"},
        "LB": {"en": "pushes high and wide on the left", "tr": "solda yüksek ve geniş konumlanır", "es": "sube alto y abierto por la izquierda"},
        "RCM": {"en": "moves into the right half-space", "tr": "sağ yarı alana kayar", "es": "ocupa el medio espacio derecho"},
        "RW": {"en": "holds the width on the right touchline", "tr": "sağ çizgide genişliği korur", "es": "fija la amplitud en la banda derecha"},
        "DM": {"en": "drops between the centre-backs to form a back three", "tr": "stoperlerin arasına düşerek üçlü savunma kurar", "es": "se incrusta entre centrales para formar línea de tres"},
        "LW": {"en": "tucks into the left half-space", "tr": "sol yarı alana içeri girer", "es": "se cierra al medio espacio izquierdo"},
    },
    "counter_5_4_1": {
        "LW": {"en": "tracks back to become a left wing-back", "tr": "geri dönerek sol kanat beki olur", "es": "baja para ser carrilero izquierdo"},
        "DM": {"en": "drops into a back five", "tr": "beşli savunmaya düşer", "es": "se incrusta en una línea de cinco"},
        "ST": {"en": "stays high as the outlet", "tr": "çıkış için önde kalır", "es": "se queda arriba como salida"},
    },
    "hold_4_3_3": {},
}
DEFAULT_ROLE = {"GK": ["GK"], "RB": ["RB"], "LB": ["LB"], "CB": ["LCB", "RCB"], "DM": ["DM"], "CM": ["LCM", "RCM"],
                "RW": ["RW"], "LW": ["LW"], "ST": ["ST"], "IRB": ["RB"]}


def lineup(match: Match, team_id: str, until: int) -> dict[str, dict[str, Any]]:
    """Role -> player on the pitch at `until` (substitutes inherit the slot; red cards remove it)."""
    team = match.team(team_id)
    slots: dict[str, str] = {}
    for p in team.players:
        if not p.starter:
            continue
        for role in DEFAULT_ROLE.get(p.position, []):
            if role not in slots:
                slots[role] = p.player_id
                break
    for e in events_until(match, until):
        if e.team_id != team_id:
            continue
        if e.event_type == "Substitution":
            for r, pid in list(slots.items()):
                if pid == e.player_id:
                    slots[r] = e.qualifiers.get("player_in", pid)
        if e.event_type == "Card" and e.outcome == "Red":
            for r, pid in list(slots.items()):
                if pid == e.player_id:
                    del slots[r]
    names = match.player_names()
    nums = {p.player_id: p.number for t in match.teams for p in t.players}
    return {r: {"player_id": pid, "name": names[pid], "number": nums[pid]} for r, pid in slots.items()}


def advantage_team(match: Match, m: MatchMoment) -> str:
    return match.opponent(m.team_id) if m.type == "red_card" else m.team_id


def response(match: Match, m: MatchMoment, until: int, locale: str, playbook: str = "amplify_3_2_5") -> dict[str, Any]:
    tid = advantage_team(match, m)
    frm, to = PLAYBOOK_SHAPE[playbook]
    lu = lineup(match, tid, until)
    texts = MOVE_TEXT[playbook]
    players = []
    for role, (x, y) in SHAPES[frm].items():
        if role not in lu:
            continue
        tx, ty = SHAPES[to].get(role, (x, y))
        players.append({"role": role, **lu[role], "from": [x, y], "to": [tx, ty],
                        "moves": role in texts, "text": texts.get(role, {}).get(locale)})
    movements = [p for p in players if p["moves"]]
    T = i18n.TACTIC[playbook]
    facts = localise(moment_facts(match, m), locale)
    actions = [Action(id=f"act-{m.id}-{p['role']}", agent="tactical_response", team_id=tid, moment_id=m.id,
                      text=f"{p['name']} ({p['role']}) {p['text']}", player_ids=[p["player_id"]]).model_dump()
               for p in movements]
    back = {"4-3-3": 4, "3-2-5": 3, "5-4-1": 5}
    front = {"4-3-3": 3, "3-2-5": 5, "5-4-1": 1}
    return {
        "moment_id": m.id, "team_id": tid, "team": match.team(tid).name, "playbook": playbook,
        "name": T["name"][locale], "from_shape": frm, "to_shape": to,
        "formation_impact": {"back_line": [back[frm], back[to]], "front_line": [front[frm], front[to]],
                             "phase": "in possession" if playbook == "amplify_3_2_5" else "out of possession"},
        "instruction": T["instruction"][locale], "risk": T["risk"][locale], "players": players,
        "movements": actions, "evidence_ids": [e.id for e in m.evidence][:6],
        "grounding": {k: facts.get(k) for k in ("share_before", "share_after", "prog_after", "shots_before", "shots_after", "ch") if k in facts},
        "options": list(PLAYBOOK_SHAPE),
    }


def what_if(match: Match, m: MatchMoment, until: int, locale: str, option: str) -> dict[str, Any]:
    if option not in PLAYBOOK_SHAPE:
        raise KeyError(option)
    facts = localise(moment_facts(match, m), locale)
    W = i18n.WHATIF[option]
    T = i18n.TACTIC[option]
    tid = advantage_team(match, m) if option != "counter_5_4_1" else match.opponent(advantage_team(match, m))
    lu = lineup(match, tid, until)
    involved = [{"role": r, **lu[r]} for r in MOVE_TEXT[option] if r in lu]
    advantage = i18n.fmt(W["advantage"][locale], facts) or W["effect"][locale]
    sc = Scenario(id=f"whatif-{m.id}-{option}", agent="tactical_response", team_id=tid, moment_id=m.id,
                  text=W["effect"][locale], player_ids=[p["player_id"] for p in involved],
                  metrics=[MetricRef(path=f"moment.{m.id}.params.{k}", value=facts[k]) for k in ("share_before", "share_after") if k in facts],
                  caveat=i18n.WHATIF["_limitations"][locale])
    return {"option": option, "name": T["name"][locale], "team": match.team(tid).name, "effect": W["effect"][locale],
            "advantage": advantage, "risk": T["risk"][locale], "players": involved,
            "limitations": i18n.WHATIF["_limitations"][locale], "score_prediction": None, "scenario": sc.model_dump()}
