"""Foundry provider + Narrative Agent with fake clients (no credentials, no network)."""
from __future__ import annotations

import json
from types import SimpleNamespace

from rely_brain import llm
from rely_brain.llm import CACHE, FoundryProvider, NoProvider, ProviderError, ResponseCache, get_provider
from rely_brain.orchestrator import run_pipeline

UNTIL = 3700


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete(self, **kw):
        self.calls.append(kw)
        if kw.get("stream"):
            return iter([SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=t))]) for t in ("Har", "bour")])
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=r))])


def provider(replies) -> tuple[FoundryProvider, FakeClient]:
    c = FakeClient(replies)
    return FoundryProvider(endpoint="https://example.invalid", api_key="test", model="test-model", client_factory=lambda: c), c


def good_reply(demo) -> str:
    m = run_pipeline(demo, UNTIL).focus()
    p = m.params
    return json.dumps({"headline": f"{p['team']} switch to the right",
                       "explanation": f"The right channel share went from {p['share_before']}% to {p['share_after']}% after Kai Okafor came on.",
                       "bullets": [f"Confidence {int(round(m.confidence * 100))}%"]})


def setup_function(_):
    CACHE._d.clear()


def test_default_provider_is_none(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    assert isinstance(get_provider(), NoProvider)
    monkeypatch.setenv("AI_PROVIDER", "microsoft_foundry")
    assert isinstance(get_provider(), FoundryProvider)


def test_foundry_requests_json_and_uses_model(demo):
    p, c = provider([good_reply(demo)])
    s = run_pipeline(demo, UNTIL, with_narrative=True, provider=p)
    assert s.narrative.source == "llm" and s.narrative.verified
    assert c.calls[0]["response_format"] == "json_object" and c.calls[0]["model"] == "test-model"
    msgs = c.calls[0]["messages"]
    assert msgs[0]["role"] == "system" and "FACTS" in msgs[1]["content"]
    t = {x.agent: x for x in s.trace}["narrative"]
    assert t.provider == "microsoft_foundry" and t.model == "test-model" and not t.fallback_used


def test_ungrounded_number_triggers_regeneration_then_success(demo):
    bad = json.dumps({"headline": "Harbour City FC surge", "explanation": "They had 97% of the ball.", "bullets": []})
    p, c = provider([bad, good_reply(demo)])
    s = run_pipeline(demo, UNTIL, with_narrative=True, provider=p)
    assert len(c.calls) == 2 and "failed verification" in c.calls[1]["messages"][1]["content"]
    assert s.narrative.source == "llm"


def test_unknown_player_twice_falls_back_to_template(demo):
    bad = json.dumps({"headline": "Big change", "explanation": "Marcus Johnson changed the game.", "bullets": []})
    p, c = provider([bad, bad])
    s = run_pipeline(demo, UNTIL, with_narrative=True, provider=p)
    assert s.narrative.source == "template" and s.focus().explanation_status == "fallback"
    t = {x.agent: x for x in s.trace}["narrative"]
    assert t.status == "fallback" and t.fallback_used


def test_provider_error_falls_back(demo):
    p, _ = provider([RuntimeError("timeout")])
    s = run_pipeline(demo, UNTIL, with_narrative=True, provider=p)
    assert s.narrative.source == "template"


def test_non_json_falls_back(demo):
    p, _ = provider(["not json", "still not json"])
    s = run_pipeline(demo, UNTIL, with_narrative=True, provider=p)
    assert s.narrative.source == "template"


def test_cache_hit_by_state_persona_locale_model(demo):
    p, c = provider([good_reply(demo)])
    run_pipeline(demo, UNTIL, with_narrative=True, provider=p)
    s2 = run_pipeline(demo, UNTIL, with_narrative=True, provider=p)
    assert len(c.calls) == 1 and s2.narrative.source == "llm"
    k1 = ResponseCache.key("h", "m", "coach", "en", "x")
    assert k1 != ResponseCache.key("h", "m", "coach", "tr", "x") != ResponseCache.key("h", "m", "fan", "en", "x")


def test_streaming_uses_sdk_stream(demo):
    p, c = provider([])
    assert "".join(p.stream_text("s", "u")) == "Harbour" and c.calls[0]["stream"] is True


def test_missing_credentials_raise_provider_error():
    p = FoundryProvider(endpoint="", api_key="")
    try:
        p.complete_json("s", "u")
        raise AssertionError("expected ProviderError")
    except ProviderError:
        pass


def test_no_secret_in_trace(demo):
    p, _ = provider([good_reply(demo)])
    s = run_pipeline(demo, UNTIL, with_narrative=True, provider=p)
    dump = json.dumps([t.model_dump() for t in s.trace])
    assert "test" not in dump.replace("test-model", "") and "example.invalid" not in dump
    assert llm.FoundryProvider.name == "microsoft_foundry"
