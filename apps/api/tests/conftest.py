from __future__ import annotations

import os

import pytest

os.environ.setdefault("AI_PROVIDER", "none")

from rely_brain.data import load_match  # noqa: E402
from rely_brain.schemas import Match  # noqa: E402

DEMO = "hcf-wva-tactical-shift"
RED = "kmr-elt-red-card"
LATE = "wva-kmr-late-comeback"
ALL = [DEMO, RED, LATE, "elt-hcf-balanced", "kmr-hcf-high-press"]


@pytest.fixture(scope="session")
def demo() -> Match:
    return load_match(DEMO)


@pytest.fixture(scope="session")
def red() -> Match:
    return load_match(RED)


@pytest.fixture(scope="session")
def late() -> Match:
    return load_match(LATE)


def truncated(m: Match, until: int) -> Match:
    """A copy of the match that physically contains only events <= until."""
    return m.model_copy(update={"events": [e for e in m.events if e.match_second <= until]})
