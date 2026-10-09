"""Deterministic narrative layer: persona x locale presentation of locale-invariant facts.

Facts are computed once (numbers, names) and never recomputed per language; templates and the
LLM only change wording. Every sentence that references a missing fact is dropped, not invented.
"""
from __future__ import annotations

from typing import Any

from . import i18n
from .schemas import Match, MatchMoment, MatchState, NarrativeOut
from .state import clock_label
from .turning_points import TH, headline_moment

WINDOW_FACTS = {"window_minutes": 10, "short_window": 5, "danger_window": TH["danger_window"] // 60}


def moment_facts(match: Match, m: MatchMoment) -> dict[str, Any]:
    """Locale-invariant facts for one moment (the only inputs a narrative may use)."""
    f: dict[str, Any] = {k: v for k, v in m.params.items() if k not in ("supporting_rules",)}
    f.setdefault("team", match.team(m.team_id).name)
    f.setdefault("opponent", match.team(match.opponent(m.team_id)).name)
    f["minute"] = m.minute
    f["clock"] = clock_label(m.timestamp)
    f["detected_clock"] = clock_label(m.detected_at)
    f["confidence_pct"] = int(round(m.confidence * 100))
    f["type"] = m.type
    f["supporting_rules"] = list(m.params.get("supporting_rules", []))
    f["after_window_complete"] = m.after_window_complete
    f.update(WINDOW_FACTS)
    return f


def localise(facts: dict[str, Any], locale: str) -> dict[str, Any]:
    p = dict(facts)
    if "channel" in p:
        p["ch"] = i18n.CHANNEL[locale][p["channel"]]
    return p


def moment_title(match: Match, m: MatchMoment, locale: str) -> str:
    p = localise(moment_facts(match, m), locale)
    return i18n.fmt(i18n.TITLE[m.type][locale], p) or m.title


def body_sentences(match: Match, m: MatchMoment, locale: str) -> list[str]:
    p = localise(moment_facts(match, m), locale)
    return [s for s in (i18n.fmt(t, p) for t in i18n.BODY[m.type][locale]) if s]


def recommendations(match: Match, m: MatchMoment, locale: str) -> list[tuple[str, str]]:
    p = localise(moment_facts(match, m), locale)
    team_rec, opp_rec = i18n.REC[m.type][locale]
    out = []
    for team, tpl in ((p["team"], team_rec), (p["opponent"], opp_rec)):
        s = i18n.fmt(tpl, p)
        if s:
            out.append((team, s))
    return out


def template_narrative(match: Match, m: MatchMoment, persona: str, locale: str) -> NarrativeOut:
    ui = i18n.UI[locale]
    facts = moment_facts(match, m)
    p = localise(facts, locale)
    head = moment_title(match, m, locale)
    body = body_sentences(match, m, locale)
    bullets: list[str] = []
    if persona == "coach":
        explanation = " ".join(body[:2])
        bullets = [f"{i18n.fmt(ui['for_team'], {'team': t})}: {r}" for t, r in recommendations(match, m, locale)]
    elif persona == "analyst":
        explanation = " ".join(body)
        bullets.append(i18n.fmt(ui["confidence"], p) or "")
        if facts["supporting_rules"]:
            rules = ", ".join(i18n.RULE_NAME[locale][r] for r in facts["supporting_rules"])
            bullets.append(i18n.fmt(ui["also"], {"rules": rules}) or "")
    elif persona == "broadcaster":
        explanation = f"{ui['talking_point']}: {body[0]}" if body else head
        if len(body) > 1:
            bullets.append(f"{ui['stat_to_show']}: {body[1]}")
    else:  # fan
        explanation = i18n.fmt(i18n.FAN[m.type][locale], p) or head
        if body:
            bullets.append(f"{ui['what_happened']}: {body[0]}")
    if facts.get("faded"):
        bullets.append(ui["faded"])
    elif not m.after_window_complete and m.type in ("sub_shift", "red_card"):
        bullets.append(ui["window_open"])
    return NarrativeOut(headline=head, explanation=explanation, bullets=[b for b in bullets if b], persona=persona,
                        locale=locale, source="template", verified=True)


# ------------------------------------------------------------------ feed / story / broadcast
def feed(match: Match, state: MatchState, moments: list[MatchMoment], locale: str, limit: int = 12) -> list[dict[str, Any]]:
    ui = i18n.UI[locale]
    names = match.player_names()
    items: list[dict[str, Any]] = []
    for m in moments:
        if m.type == "goal":
            items.append({"id": m.id, "second": m.timestamp, "clock": clock_label(m.timestamp), "kind": "goal", "severity": "high",
                          "team_id": m.team_id, "moment_id": m.id,
                          "text": i18n.fmt(ui["goal_feed"], {"team": match.team(m.team_id).short, "player": m.params.get("player", "")})})
        else:
            items.append({"id": m.id, "second": m.detected_at, "clock": clock_label(m.detected_at), "kind": "moment", "severity": m.severity,
                          "team_id": m.team_id, "moment_id": m.id, "text": moment_title(match, m, locale),
                          "confidence": m.confidence})
    seen_moment_events = {m.trigger.get("event_id") for m in moments}
    from .data import events_until

    for e in events_until(match, state.until):
        if e.event_id in seen_moment_events:
            continue
        team = match.team(e.team_id).short
        if e.event_type == "Substitution":
            text = i18n.fmt(ui["sub"], {"player_in": names.get(e.qualifiers.get("player_in", ""), ""),
                                         "player_out": names.get(e.player_id or "", ""), "team": team})
            items.append({"id": e.event_id, "second": e.match_second, "clock": clock_label(e.match_second), "kind": "sub",
                          "severity": "low", "team_id": e.team_id, "moment_id": None, "text": text})
        elif e.event_type == "Card" and e.outcome == "Red":
            items.append({"id": e.event_id, "second": e.match_second, "clock": clock_label(e.match_second), "kind": "card",
                          "severity": "high", "team_id": e.team_id, "moment_id": None,
                          "text": i18n.fmt(ui["red"], {"player": names.get(e.player_id or "", ""), "team": team})})
    items.sort(key=lambda x: (-x["second"], x["id"]))
    return items[:limit]


def story_chapters(match: Match, moments: list[MatchMoment], locale: str) -> list[dict[str, Any]]:
    """Match Story: one chapter per evidenced moment (no chapter without evidence)."""
    chapters = []
    for m in sorted(moments, key=lambda x: x.timestamp):
        if not m.evidence:
            continue
        body = body_sentences(match, m, locale)
        chapters.append({"moment_id": m.id, "clock": clock_label(m.timestamp), "title": moment_title(match, m, locale),
                         "summary": body[0] if body else "", "evidence_ids": [e.id for e in m.evidence][:6]})
    return chapters


def story_cards(match: Match, moments: list[MatchMoment], locale: str) -> list[dict[str, Any]]:
    cards = []
    for m in moments:
        if m.type == "goal":
            continue
        body = body_sentences(match, m, locale)
        cards.append({"moment_id": m.id, "clock": clock_label(m.detected_at), "title": moment_title(match, m, locale),
                      "stat": body[1] if len(body) > 1 else (body[0] if body else ""), "context": body[0] if body else "",
                      "evidence_ids": [e.id for e in m.evidence][:6]})
    return cards[-4:]


def commentator_prep(match: Match, state: MatchState, locale: str) -> list[str]:
    lab = {"en": ("Most involved", "touches", "Substitutions so far", "Cards", "Pass share"),
           "tr": ("En çok topla buluşan", "temas", "Yapılan değişiklikler", "Kartlar", "Pas payı"),
           "es": ("Más participativo", "contactos", "Cambios realizados", "Tarjetas", "Cuota de pases")}[locale]
    h, a = match.home_team_id, match.away_team_id
    notes = []
    if state.player_involvement:
        top = state.player_involvement[0]
        notes.append(f"{lab[0]}: {top.name} ({match.team(top.team_id).short}), {top.touches} {lab[1]}")
    th, ta = state.teams[h], state.teams[a]
    notes.append(f"{lab[2]}: {match.team(h).short} {th.substitutions}, {match.team(a).short} {ta.substitutions}")
    notes.append(f"{lab[3]}: {match.team(h).short} {th.yellow_cards}+{th.red_cards}, {match.team(a).short} {ta.yellow_cards}+{ta.red_cards}")
    notes.append(f"{lab[4]}: {match.team(h).short} {int(round(th.possession * 100))}%, {match.team(a).short} {int(round(ta.possession * 100))}%")
    return notes


# ------------------------------------------------------------------ recaps
def recap_facts(match: Match, state: MatchState, moments: list[MatchMoment]) -> dict[str, Any]:
    h, a = match.home_team_id, match.away_team_id
    th, ta = state.teams[h], state.teams[a]
    names = match.player_names()
    goals = [m for m in moments if m.type == "goal"]
    head = headline_moment(moments)
    return {
        "home": match.team(h).name, "away": match.team(a).name, "home_goals": th.goals, "away_goals": ta.goals,
        "home_shots": th.shots, "away_shots": ta.shots, "home_sot": th.shots_on_target, "away_sot": ta.shots_on_target,
        "home_poss": int(round(th.possession * 100)), "away_poss": int(round(ta.possession * 100)),
        "home_entries": th.final_third_entries, "away_entries": ta.final_third_entries,
        "goals": [{"minute": g.minute, "player": names.get(g.trigger.get("player_id") or "", ""), "team": match.team(g.team_id).short} for g in goals],
        "headline_id": head.id if head else None, "clock": state.clock, "full_time": state.is_full_time,
    }


def recaps(match: Match, state: MatchState, moments: list[MatchMoment], locale: str) -> dict[str, Any]:
    f = recap_facts(match, state, moments)
    R = i18n.RECAP[locale]
    head = next((m for m in moments if m.id == f["headline_id"]), None)
    head_title = moment_title(match, head, locale) if head else ""
    goal_list = ", ".join(f"{g['player']} {g['minute']}' ({g['team']})" for g in f["goals"])
    result = i18n.fmt(R["result"], f) or ""
    goals_line = (i18n.fmt(R["goals"], {"list": goal_list}) or "") + "." if f["goals"] else R["no_goals"]
    decisive = i18n.fmt(R["decisive"], {"title": head_title}) if head else ""
    stats = i18n.fmt(R["stats"], f) or ""
    status = R["ft"] if f["full_time"] else i18n.fmt(R["partial"], f)
    key = [m for m in moments if m.type != "goal"]
    key_lines = []
    for m in [k for k in key if not head or k.id != head.id][-4:]:
        b = body_sentences(match, m, locale)
        key_lines.append(f"{clock_label(m.detected_at)} {moment_title(match, m, locale)}. {b[0] if b else ''}".strip())
    head_body = body_sentences(match, head, locale) if head else []
    winner = f["home"] if f["home_goals"] > f["away_goals"] else (f["away"] if f["away_goals"] > f["home_goals"] else None)
    fan_line = i18n.fmt(R["fan_win"], {"winner": winner}) if winner else R["fan_draw"]
    coach_lines = [R["coach_intro"]]
    for m in key[-3:]:
        for _team, rec in recommendations(match, m, locale)[:1]:
            coach_lines.append(f"- {moment_title(match, m, locale)}: {rec}")
    cards = story_cards(match, moments, locale)
    social = i18n.fmt(R["social"], {**f, "title": head_title}) or result
    if len(social) > 280:
        social = social[:277] + "..."
    return {
        "status": status, "facts": f,
        "thirty_seconds": " ".join(x for x in (result + ".", goals_line, decisive) if x),
        "analyst_two_minutes": "\n".join([result + ".", goals_line, stats, decisive, *(head_body[:2]), R["key_moments"] + ":", *key_lines]),
        "coach": "\n".join([result + ".", *coach_lines]),
        "broadcast": "\n".join([i18n.fmt(R["broadcast_intro"], f) or "", result + ".", goals_line,
                                *[f"{c['clock']} {c['title']}: {c['stat']}" for c in cards]]),
        "fan": " ".join(x for x in (fan_line, result + ".", goals_line, i18n.fmt(i18n.FAN[head.type][locale], localise(moment_facts(match, head), locale)) if head else "") if x),
        "social": social,
    }
