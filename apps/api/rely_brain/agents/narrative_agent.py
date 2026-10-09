"""Narrative Agent: persona- and locale-specific explanation of one verified moment.

With AI_PROVIDER=microsoft_foundry it asks the Foundry model for structured JSON, then the
Evidence Verifier checks numeric grounding and entities. One regeneration with the issues
listed; if it still fails (or the call errors/times out) the deterministic template is used.
"""
from __future__ import annotations

import json

from .. import i18n
from ..llm import CACHE, ProviderError
from ..narrative import localise, moment_facts, template_narrative
from ..schemas import NarrativeOut
from .base import Agent, SharedState
from .verifier import EvidenceVerifierAgent

LANG = {"en": "English", "tr": "Turkish", "es": "Spanish"}
STYLE = {
    "coach": "Practical and direct. One-sentence diagnosis, then two concrete instructions (one per team).",
    "analyst": "Precise and metric-led. State before/after values and the window. Mention confidence.",
    "broadcaster": "Vivid but factual on-air language. One talking point and one stat to show on screen.",
    "fan": "Simple, warm language for a casual fan. Max one number.",
}
SYSTEM = (
    "You are the Narrative Agent of Rely Match Brain, a football reasoning system working on SYNTHETIC match data. "
    "Explain why the match changed using ONLY the FACTS provided. Rules: (1) every number you write must appear in FACTS; "
    "(2) only mention people and teams listed in ENTITIES; (3) do not predict scores; (4) write in the requested language; "
    "(5) respond with a JSON object: {\"headline\": str, \"explanation\": str, \"bullets\": [str, ...]} (max 3 bullets)."
)


class NarrativeAgent(Agent):
    name = "narrative"
    uses_llm = True

    def __init__(self) -> None:
        self.fallback_used = False
        self.note: str | None = None

    def build_prompt(self, s: SharedState, facts: dict, issues: list[str] | None = None) -> str:
        entities = EvidenceVerifierAgent.known_entities(s)
        recs = [c.text for c in s.tactical if c.kind == "recommendation" and c.moment_id == s.focus_moment_id]
        payload = {"persona": s.persona, "style": STYLE[s.persona], "language": LANG[s.locale], "FACTS": facts,
                   "ENTITIES": entities, "verified_recommendations": recs}
        msg = json.dumps(payload, ensure_ascii=False, default=str)
        if issues:
            msg += "\nYour previous answer failed verification: " + "; ".join(issues) + ". Fix these and answer again."
        return msg

    def run(self, s: SharedState) -> int:
        if "narrative" in s.fail:
            raise RuntimeError("simulated Narrative failure")
        m = s.focus()
        if m is None:
            return 0
        assert s.state is not None
        facts = localise(moment_facts(s.match, m), s.locale)
        if s.provider.name == "none":
            s.narrative = template_narrative(s.match, m, s.persona, s.locale)
            m.explanation_status = "generated"
            self.note = "template (AI_PROVIDER=none)"
            return 1
        key = CACHE.key(s.state.state_hash, m.id, s.persona, s.locale, s.provider.model)
        cached = CACHE.get(key)
        if cached is not None:
            s.narrative = cached
            m.explanation_status = "generated"
            self.note = "cache hit"
            return 1
        issues: list[str] | None = None
        for attempt in range(2):
            try:
                data = s.provider.complete_json(SYSTEM, self.build_prompt(s, facts, issues))
            except ProviderError as exc:
                self.note = str(exc)
                break
            head = str(data.get("headline", "")).strip()
            expl = str(data.get("explanation", "")).strip()
            bullets = [str(b) for b in data.get("bullets", [])][:3] if isinstance(data.get("bullets"), list) else []
            if not head or not expl:
                issues = ["missing headline or explanation"]
                continue
            issues = EvidenceVerifierAgent.check_text(s, [head, expl, *bullets], facts)
            if not issues:
                out = NarrativeOut(headline=head, explanation=expl, bullets=bullets, persona=s.persona, locale=s.locale,
                                   source="llm", verified=True)
                CACHE.put(key, out)
                s.narrative = out
                m.explanation_status = "generated"
                self.note = f"llm verified on attempt {attempt + 1}"
                return 1
            self.note = "verification failed: " + "; ".join(issues[:3])
        # Deterministic, grounded fallback.
        self.fallback_used = True
        s.narrative = template_narrative(s.match, m, s.persona, s.locale)
        m.explanation_status = "fallback"
        return 1


def unavailable_text(locale: str) -> str:
    return i18n.UI[locale]["unavailable"]
