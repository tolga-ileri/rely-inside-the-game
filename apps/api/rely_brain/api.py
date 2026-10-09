"""FastAPI app for Rely Match Brain."""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import narrative as nar
from .agents.narrative_agent import SYSTEM, NarrativeAgent, unavailable_text
from .data import DEMO_MATCH_ID, list_matches, load_match
from .evidence_i18n import localise_label
from .llm import ProviderError, get_provider
from .logging_setup import setup_logging
from .orchestrator import run_pipeline
from .schemas import LOCALES, PERSONAS, Match, MatchMoment
from .state import clock_label
from .tactics import PLAYBOOK_SHAPE, response, what_if
from .turning_points import detect, headline_moment

setup_logging()
log = logging.getLogger("rely.api")
VALID_FAIL = {"event_analyst", "tactical_analyst", "evidence_verifier", "narrative"}

app = FastAPI(title="Rely Match Brain API", version="1.0.0",
              description="Event-driven football reasoning on synthetic football-realistic data.")
app.add_middleware(CORSMiddleware,
                   allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://127.0.0.1:3100,http://localhost:3100").split(",") if o.strip()],
                   allow_methods=["GET", "POST"], allow_headers=["*"])


@app.middleware("http")
async def timing(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    ms = round((time.perf_counter() - t0) * 1000, 2)
    resp.headers["Server-Timing"] = f"app;dur={ms}"
    log.info("request", extra={"path": request.url.path, "status": resp.status_code, "ms": ms})
    return resp


def _match(match_id: str) -> Match:
    try:
        return load_match(match_id)
    except KeyError as exc:
        raise HTTPException(404, f"unknown match {match_id}") from exc


def _check(persona: str, locale: str) -> None:
    if persona not in PERSONAS:
        raise HTTPException(422, "persona must be one of " + ", ".join(PERSONAS))
    if locale not in LOCALES:
        raise HTTPException(422, "locale must be one of " + ", ".join(LOCALES))


def _fail(fail: str | None) -> set[str]:
    return {f for f in (fail or "").split(",") if f in VALID_FAIL}


def _moment_view(match: Match, m: MatchMoment, locale: str) -> dict[str, Any]:
    d = m.model_dump()
    d["title_localized"] = nar.moment_title(match, m, locale)
    for ev in d.get("evidence", []):
        ev["label"] = localise_label(ev["label"], locale)
    d["clock"] = clock_label(m.timestamp)
    d["detected_clock"] = clock_label(m.detected_at)
    return d


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, Any]:
    try:
        load_match(DEMO_MATCH_ID)
        ok = True
    except Exception:  # noqa: BLE001
        ok = False
    p = get_provider()
    return {"ready": ok, "matches": len(list_matches()), "ai_provider": p.name, "model": p.model}


@app.get("/api/matches")
def matches() -> list[dict]:
    return list_matches()


@app.get("/api/matches/{match_id}")
def match_meta(match_id: str) -> dict[str, Any]:
    m = _match(match_id)
    d = m.model_dump(exclude={"events"})
    d["data_label"] = "SYNTHETIC FOOTBALL-REALISTIC DATA"
    return d


@app.get("/api/matches/{match_id}/keymoments")
def keymoments(match_id: str) -> dict[str, Any]:
    """Navigation index (whole match) used only for seeking: Jump to Key Moment / HT / FT."""
    m = _match(match_id)
    ms = detect(m, m.duration_seconds)
    head = headline_moment(ms)
    return {"headline": {"id": head.id, "detected_at": head.detected_at, "timestamp": head.timestamp} if head else None,
            "markers": [{"id": x.id, "type": x.type, "second": x.detected_at if x.type != "goal" else x.timestamp,
                         "team_id": x.team_id, "severity": x.severity} for x in ms],
            "half_time": 2700, "full_time": m.duration_seconds, "demo": m.demo}


@app.get("/api/matches/{match_id}/live")
def live(match_id: str, until: int = Query(0, ge=0), locale: str = "en", persona: str = "analyst",
         fail: str | None = None) -> dict[str, Any]:
    _check(persona, locale)
    m = _match(match_id)
    s = run_pipeline(m, until, persona, locale, fail=_fail(fail))
    st = s.state
    assert st is not None
    head = headline_moment(s.moments)
    return {
        "state": st.model_dump(), "moments": [_moment_view(m, x, locale) for x in s.moments],
        "headline_id": head.id if head else None, "feed": nar.feed(m, st, s.moments, locale),
        "observations": [c.model_dump() for c in s.observations], "tactical": [c.model_dump() for c in s.tactical],
        "verification": s.verification.model_dump() if s.verification else None,
        "trace": [t.model_dump() for t in s.trace], "chapters": nar.story_chapters(m, s.moments, locale),
    }


@app.get("/api/matches/{match_id}/explain")
def explain(match_id: str, until: int = Query(..., ge=0), moment_id: str | None = None, persona: str = "analyst",
            locale: str = "en", fail: str | None = None) -> dict[str, Any]:
    _check(persona, locale)
    m = _match(match_id)
    s = run_pipeline(m, until, persona, locale, moment_id=moment_id, with_narrative=True, provider=get_provider(), fail=_fail(fail))
    focus = s.focus()
    if focus is None:
        raise HTTPException(404, "no moment detected yet at this point of the match")
    ids = set(focus.linked_event_ids) | {eid for ev in focus.evidence for eid in ev.event_ids}
    events = [e.model_dump() for e in m.events if e.event_id in ids and e.match_second <= until]
    st = s.state
    assert st is not None
    return {
        "moment": _moment_view(m, focus, locale), "narrative": s.narrative.model_dump() if s.narrative else None,
        "explanation_unavailable": None if s.narrative else unavailable_text(locale),
        "claims": [c.model_dump() for c in s.claims if c.moment_id == focus.id],
        "verification": s.verification.model_dump() if s.verification else None,
        "trace": [t.model_dump() for t in s.trace], "events": events,
        "story_cards": nar.story_cards(m, s.moments, locale), "commentator_prep": nar.commentator_prep(m, st, locale),
    }


@app.get("/api/matches/{match_id}/explain/stream")
def explain_stream(match_id: str, until: int = Query(..., ge=0), moment_id: str | None = None, persona: str = "analyst",
                   locale: str = "en") -> StreamingResponse:
    """SSE. Streams model tokens when the provider supports streaming; the verified result is always sent last."""
    _check(persona, locale)
    m = _match(match_id)
    provider = get_provider()
    s = run_pipeline(m, until, persona, locale, moment_id=moment_id, with_narrative=False, provider=provider)
    focus = s.focus()

    def gen():
        if focus is None:
            yield "event: error\ndata: {}\n\n"
            return
        if provider.supports_stream:
            from .narrative import localise, moment_facts

            facts = localise(moment_facts(m, focus), locale)
            try:
                for tok in provider.stream_text(SYSTEM, NarrativeAgent().build_prompt(s, facts)):
                    yield f"event: token\ndata: {json.dumps(tok)}\n\n"
            except ProviderError as exc:
                yield f"event: notice\ndata: {json.dumps(str(exc))}\n\n"
        final = run_pipeline(m, until, persona, locale, moment_id=focus.id, with_narrative=True, provider=provider)
        payload = final.narrative.model_dump() if final.narrative else {"unavailable": unavailable_text(locale)}
        yield f"event: final\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


class ResponseReq(BaseModel):
    until: int
    moment_id: str | None = None
    locale: str = "en"
    playbook: str = "amplify_3_2_5"


class WhatIfReq(BaseModel):
    until: int
    moment_id: str | None = None
    locale: str = "en"
    option: str = "amplify_3_2_5"


def _focus(m: Match, until: int, moment_id: str | None) -> MatchMoment:
    ms = detect(m, until)
    mm = next((x for x in ms if x.id == moment_id), None) if moment_id else headline_moment(ms)
    if mm is None or mm.type == "goal":
        raise HTTPException(404, "no turning point available for a tactical response")
    return mm


@app.post("/api/matches/{match_id}/response")
def tactical_response(match_id: str, req: ResponseReq) -> dict[str, Any]:
    _check("coach", req.locale)
    if req.playbook not in PLAYBOOK_SHAPE:
        raise HTTPException(422, "unknown playbook")
    m = _match(match_id)
    t0 = time.perf_counter()
    out = response(m, _focus(m, req.until, req.moment_id), req.until, req.locale, req.playbook)
    log.info("tactical_response", extra={"match_id": match_id, "ms": round((time.perf_counter() - t0) * 1000, 2)})
    return out


@app.post("/api/matches/{match_id}/whatif")
def whatif(match_id: str, req: WhatIfReq) -> dict[str, Any]:
    _check("coach", req.locale)
    m = _match(match_id)
    try:
        return what_if(m, _focus(m, req.until, req.moment_id), req.until, req.locale, req.option)
    except KeyError as exc:
        raise HTTPException(422, "unknown option") from exc


@app.get("/api/matches/{match_id}/recap")
def recap(match_id: str, until: int = Query(..., ge=0), locale: str = "en") -> dict[str, Any]:
    _check("analyst", locale)
    m = _match(match_id)
    s = run_pipeline(m, until, "analyst", locale)
    assert s.state is not None
    return nar.recaps(m, s.state, s.moments, locale)
