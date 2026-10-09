"""Grounding guard: score pairs, causal wording and numbers in generated text."""
from rely_brain.guard import causal_claims, ungrounded_numbers, ungrounded_scores


def test_invented_score_is_rejected_even_when_its_digits_exist_elsewhere():
    # 5 and 0 may both occur in the facts; the pair 5-0 is still not the match score.
    assert ungrounded_scores("They lead 5-0 and are unstoppable.", [3, 3]) == ["5-0"]


def test_real_score_and_formations_pass():
    assert ungrounded_scores("Level at 3-3, now shaping as a 3-2-5 in possession.", [3, 3]) == []
    assert ungrounded_scores("The score is 1 – 0 to the home side.", [0, 1]) == []


def test_definitive_causal_wording_is_flagged_but_association_language_is_not():
    assert causal_claims("The substitution caused the collapse.") == ["caused"]
    assert causal_claims("After the substitution, right-side entries rose.") == []


def test_numbers_outside_the_facts_are_still_flagged():
    assert ungrounded_numbers("The equaliser came at 97'.", {56.0, 60.0}) == ["97"]
