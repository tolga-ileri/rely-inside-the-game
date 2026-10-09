"""Loading synthetic matches from synthetic-data/matches (read-only, cached)."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from .schemas import Event, Match

_DEFAULT = Path(__file__).resolve().parents[3] / "synthetic-data" / "matches"
DEMO_MATCH_ID = "hcf-wva-tactical-shift"


def matches_dir() -> Path:
    env = os.getenv("RELY_MATCHES_DIR")
    if env:
        p = Path(env)
        if not p.is_absolute():
            p = (Path(__file__).resolve().parents[1] / p).resolve()
        return p
    return _DEFAULT


@lru_cache(maxsize=16)
def load_match(match_id: str) -> Match:
    path = matches_dir() / f"{match_id}.json"
    if not path.exists() or path.parent.resolve() != matches_dir().resolve():
        raise KeyError(match_id)
    return Match.model_validate(json.loads(path.read_text(encoding="utf-8")))


def list_matches() -> list[dict]:
    idx = matches_dir() / "index.json"
    return json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []


def events_until(match: Match, until: int) -> list[Event]:
    """The ONLY way the engine sees events: everything strictly at or before `until`."""
    return [e for e in match.events if e.match_second <= until]
