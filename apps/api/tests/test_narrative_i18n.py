from __future__ import annotations

import pytest

from rely_brain import narrative as nar
from rely_brain.guard import NUM_RE, normalise_number
from rely_brain.orchestrator import run_pipeline
from rely_brain.schemas import LOCALES, PERSONAS
from rely_brain.state import compute_state
from rely_brain.turning_points import detect, headline_moment

UNTIL = 3700


def numbers(text: str) -> list[float]:
    return sorted(normalise_number(t) for t in NUM_RE.findall(text))


def test_facts_are_locale_invariant(demo):
    m = headline_moment(detect(demo, UNTIL))
    base = nar.moment_facts(demo, m)
    for loc in LOCALES:
        f = nar.localise(nar.moment_facts(demo, m), loc)
        assert {k: v for k, v in f.items() if k != "ch"} == base


@pytest.mark.parametrize("persona", PERSONAS)
def test_language_changes_wording_not_numbers(demo, persona):
    outs = {}
    for loc in LOCALES:
        s = run_pipeline(demo, UNTIL, persona=persona, locale=loc, with_narrative=True)
        n = s.narrative
        outs[loc] = n
        assert n.locale == loc and n.verified
    en = numbers(outs["en"].headline + " " + outs["en"].explanation)
    for loc in ("tr", "es"):
        assert numbers(outs[loc].headline + " " + outs[loc].explanation) == en
        assert outs[loc].explanation != outs["en"].explanation


def test_language_does_not_recompute_state(demo):
    a = run_pipeline(demo, UNTIL, locale="en")
    b = run_pipeline(demo, UNTIL, locale="tr")
    assert a.state.model_dump() == b.state.model_dump()
    assert [m.model_dump() for m in a.moments] == [m.model_dump() for m in b.moments]
    assert [c.model_dump() for c in a.claims] == [c.model_dump() for c in b.claims]


def test_personas_share_evidence_but_differ(demo):
    texts = set()
    for p in PERSONAS:
        s = run_pipeline(demo, UNTIL, persona=p, with_narrative=True)
        texts.add(s.narrative.explanation)
        assert s.focus().id == run_pipeline(demo, UNTIL, persona="analyst").focus().id
    assert len(texts) == 4
    coach = run_pipeline(demo, UNTIL, persona="coach", with_narrative=True).narrative
    assert any("Harbour City FC" in b for b in coach.bullets)


def test_template_narrative_is_grounded(demo):
    from rely_brain.agents.verifier import EvidenceVerifierAgent

    for loc in LOCALES:
        for p in PERSONAS:
            s = run_pipeline(demo, UNTIL, persona=p, locale=loc, with_narrative=True)
            n = s.narrative
            facts = nar.localise(nar.moment_facts(demo, s.focus()), loc)
            assert EvidenceVerifierAgent.check_text(s, [n.headline, n.explanation, *n.bullets], facts) == [], (p, loc)


def test_recaps_all_formats_and_locales(demo):
    st = compute_state(demo, demo.duration_seconds)
    ms = detect(demo, demo.duration_seconds)
    for loc in LOCALES:
        r = nar.recaps(demo, st, ms, loc)
        for k in ("thirty_seconds", "analyst_two_minutes", "coach", "broadcast", "fan", "social"):
            assert r[k], (k, loc)
        assert len(r["social"]) <= 280
        assert "2-1" in r["thirty_seconds"]
    en, tr = nar.recaps(demo, st, ms, "en"), nar.recaps(demo, st, ms, "tr")
    assert en["facts"] == tr["facts"]


def test_feed_is_compact_and_chapters_have_evidence(demo):
    st = compute_state(demo, demo.duration_seconds)
    ms = detect(demo, demo.duration_seconds)
    f = nar.feed(demo, st, ms, "en")
    assert 0 < len(f) <= 12
    assert [x["second"] for x in f] == sorted([x["second"] for x in f], reverse=True)
    for ch in nar.story_chapters(demo, ms, "es"):
        assert ch["evidence_ids"]
