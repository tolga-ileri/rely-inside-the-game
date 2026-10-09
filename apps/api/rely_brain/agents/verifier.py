"""Evidence Verification Agent.

Checks every claim's metrics, events, players and timestamps against data available at `until`:
- metric refs are re-resolved (windows recomputed from raw events <= until) and compared
- event ids must exist and be at or before `until` (no future leakage)
- player ids must be in the match roster
- timestamps must be <= until
Hypotheses are causal statements: their evidence is checked, but they count as "unverifiable",
so evidence coverage = supported / total claims is honest and not forced to 100%.
Also provides text checks for generated narratives: numeric grounding + entity validation.
"""
from __future__ import annotations

from typing import Any

from ..data import events_until
from ..guard import allowed_numbers, ungrounded_numbers, unknown_entities
from ..schemas import Claim, MatchMoment, VerificationReport, WindowMetrics
from ..windows import window_metrics
from .base import Agent, SharedState


def _wfield(w: WindowMetrics, fld: str) -> Any:
    if fld.startswith("prog_share_"):
        return round(w.prog_share(fld[-1]), 3)
    return getattr(w, fld)


class Resolver:
    def __init__(self, s: SharedState):
        self.s = s
        st = s.state
        assert st is not None
        self.evs = events_until(s.match, st.until)
        self.event_ids = {e.event_id for e in self.evs}
        self.moments: dict[str, MatchMoment] = {m.id: m for m in s.moments}
        self.roster = {p.player_id for t in s.match.teams for p in t.players}

    def resolve(self, path: str) -> Any:
        st = self.s.state
        assert st is not None
        parts = path.split(".")
        if parts[0] == "state":
            if parts[1] == "momentum":
                return st.momentum
            if parts[1] in ("last5", "last10"):
                w = getattr(st, parts[1])[parts[2]]
                return _wfield(window_metrics(self.evs, parts[2], w.start, w.end), parts[3])
            if parts[1] == "teams":
                return getattr(st.teams[parts[2]], parts[3])
            if parts[1] == "player":
                p = next((x for x in st.player_involvement if x.player_id == parts[2]), None)
                return getattr(p, parts[3]) if p else None
        if parts[0] == "moment":
            mid, which, fld = ".".join(parts[1:-2]), parts[-2], parts[-1]
            m = self.moments.get(mid)
            w = (m.before_state if which == "before" else m.after_state) if m else None
            if w is None:
                return None
            if w.end > st.until + 1:
                raise ValueError("window extends past until")
            return _wfield(window_metrics(self.evs, w.team_id, w.start, w.end), fld)
        if parts[0] == "window":
            tid, start, end, fld = parts[1], int(parts[2]), int(parts[3]), parts[4]
            if end > st.until + 1:
                raise ValueError("window extends past until")
            return _wfield(window_metrics(self.evs, tid, start, end), fld)
        raise KeyError(path)


def _equal(a: Any, b: Any) -> bool:
    if isinstance(a, int | float) and isinstance(b, int | float):
        return abs(float(a) - float(b)) <= 0.006
    return a == b


class EvidenceVerifierAgent(Agent):
    name = "evidence_verifier"

    def verify_claim(self, c: Claim, r: Resolver) -> str:
        st = self.s_until
        notes: list[str] = []
        for ref in c.metrics:
            try:
                actual = r.resolve(ref.path)
            except (KeyError, ValueError, AttributeError, IndexError) as exc:
                notes.append(f"unresolvable metric {ref.path} ({type(exc).__name__})")
                continue
            if not _equal(actual, ref.value):
                notes.append(f"metric mismatch {ref.path}: claimed {ref.value}, actual {actual}")
        for eid in c.event_ids:
            if eid not in r.event_ids:
                notes.append(f"unknown or future event {eid}")
        for pid in c.player_ids:
            if pid not in r.roster:
                notes.append(f"unknown player {pid}")
        for ts in c.timestamps:
            if ts > st:
                notes.append(f"timestamp {ts} after cut-off {st}")
        c.verification_notes = notes
        if notes:
            c.verified = False
            return "rejected"
        if not c.metrics and not c.event_ids:
            c.verified = None
            return "unverifiable"
        c.verified = True
        return "unverifiable" if c.kind == "hypothesis" else "supported"

    def run(self, s: SharedState) -> int:
        if "evidence_verifier" in s.fail:
            raise RuntimeError("simulated Evidence Verifier failure")
        assert s.state is not None
        self.s_until = s.state.until
        r = Resolver(s)
        counts = {"supported": 0, "rejected": 0, "unverifiable": 0}
        issues: list[str] = []
        for c in s.claims:
            status = self.verify_claim(c, r)
            counts[status] += 1
            issues += [f"{c.id}: {n}" for n in c.verification_notes]
        total = sum(counts.values())
        s.verification = VerificationReport(total_claims=total, supported=counts["supported"], rejected=counts["rejected"],
                                            unverifiable=counts["unverifiable"],
                                            coverage=round(counts["supported"] / total, 3) if total else 0.0, issues=issues[:20])
        # Rejected claims are removed from what downstream agents may use.
        s.observations = [c for c in s.observations if c.verified is not False]
        s.tactical = [c for c in s.tactical if c.verified is not False]
        return total

    # ------------------------------------------------------------- narrative text checks
    @staticmethod
    def known_entities(s: SharedState) -> list[str]:
        names = [p.name for t in s.match.teams for p in t.players]
        teams = [t.name for t in s.match.teams] + [t.short for t in s.match.teams]
        return names + teams

    @classmethod
    def check_text(cls, s: SharedState, texts: list[str], facts: dict[str, Any]) -> list[str]:
        allowed = allowed_numbers(facts.values())
        known = cls.known_entities(s)
        issues: list[str] = []
        for t in texts:
            for n in ungrounded_numbers(t, allowed):
                issues.append(f"ungrounded number '{n}'")
            for e in unknown_entities(t, known):
                issues.append(f"unknown entity '{e}'")
        return issues
