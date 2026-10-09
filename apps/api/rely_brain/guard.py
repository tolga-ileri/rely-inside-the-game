"""Grounding guards: numeric grounding and entity validation for generated text."""
from __future__ import annotations

import re
from collections.abc import Iterable

NUM_RE = re.compile(r"(?<![\w.])[-+]?\d+(?:[.,]\d+)?")
# Two or more consecutive capitalised words (Unicode letters), e.g. "Kai Okafor", "John Smith".
CAP_SEQ_RE = re.compile(r"\b([A-ZÀ-ÖØ-ÞĞİŞÇÜÖ][\w'’-]+(?:\s+[A-ZÀ-ÖØ-ÞĞİŞÇÜÖ][\w'’-]+)+)")
ALLOWED_CAPS = {
    "Rely", "Match", "Brain", "Momentum", "Coach", "Analyst", "Broadcaster", "Fan", "Recap", "Full", "Time", "Goal", "GOAL", "GOL",
    "Red", "Yellow", "Card", "For", "The", "A", "An", "In", "On", "At", "Since", "Before", "After", "Shots", "Box", "Last", "Key",
    "What", "Talking", "Stat", "Confidence", "Also", "Final", "Third", "Para", "El", "La", "Los", "Las", "Desde", "Antes", "Tiros",
    "Gol", "Goles", "Bu", "Son", "Şutlar", "Değişiklikten", "Kırmızı", "Sarı", "Kart", "Qué", "Dato", "Tema", "Ne", "Rule", "Evidence",
    "Moment", "Window", "Synthetic", "Football", "Data", "xG", "I", "It", "They", "He", "Keep", "Shift", "Press", "Use", "Defend",
    "Settle", "Stretch", "Sustain", "Slow", "Break", "Compress", "Manage", "Respond", "Right", "Left", "Centre", "Center",
}


def normalise_number(tok: str) -> float | None:
    tok = tok.replace(",", ".")
    try:
        return float(tok)
    except ValueError:
        return None


def allowed_numbers(values: Iterable) -> set[float]:
    out: set[float] = set()
    for v in values:
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, int | float):
            out.add(round(float(v), 2))
        elif isinstance(v, str):
            for m in NUM_RE.findall(v):
                n = normalise_number(m)
                if n is not None:
                    out.add(round(n, 2))
        elif isinstance(v, list | tuple):
            out |= allowed_numbers(v)
        elif isinstance(v, dict):
            out |= allowed_numbers(v.values())
    return out


FORMATION_RE = re.compile(r"(?<![\d.])\d(?:-\d){2,3}(?!\d)")


def ungrounded_numbers(text: str, allowed: set[float]) -> list[str]:
    """Numbers in `text` not present in the facts. Formation names (4-3-3) are vocabulary, not metrics."""
    bad = []
    for tok in NUM_RE.findall(FORMATION_RE.sub(" ", text)):
        n = normalise_number(tok)
        if n is None:
            continue
        if not any(abs(abs(n) - a) < 0.011 for a in allowed):
            bad.append(tok)
    return bad


def unknown_entities(text: str, known: Iterable[str]) -> list[str]:
    """Capitalised multi-word names that are not known players/teams (after removing known spans)."""
    scrub = text
    for k in sorted(set(known), key=len, reverse=True):
        if k:
            scrub = scrub.replace(k, " · ")
    bad = []
    for seq in CAP_SEQ_RE.findall(scrub):
        words = seq.split()
        unknown = [w for w in words if w.strip("'’-") not in ALLOWED_CAPS]
        if len(unknown) >= 2:
            bad.append(seq)
    return bad
