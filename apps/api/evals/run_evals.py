"""AI evaluation suite for Rely Match Brain.

Runs offline and deterministically (template narratives + scripted fake LLM replies to probe the
guards). It does NOT call Azure AI Foundry. Writes evals/report.md and evals/report.json.

    python -m evals.run_evals            # full suite (5 matches)
    python -m evals.run_evals --smoke    # demo match only (CI)
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from types import SimpleNamespace

from rely_brain import narrative as nar
from rely_brain.agents.verifier import EvidenceVerifierAgent
from rely_brain.data import list_matches, load_match
from rely_brain.guard import NUM_RE
from rely_brain.llm import CACHE, FoundryProvider
from rely_brain.orchestrator import run_pipeline
from rely_brain.schemas import LOCALES, PERSONAS, Recommendation
from rely_brain.turning_points import detect, headline_moment

OUT = Path(__file__).resolve().parent
EN_STOP = re.compile(r"\b(the|and|since|before|after|shots|of|with)\b", re.I)


class ScriptedClient:
    def __init__(self, replies: list):
        self.replies = list(replies)

    def complete(self, **kw):
        r = self.replies.pop(0) if self.replies else "{}"
        if isinstance(r, Exception):
            raise r
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=r))])


def fake(replies: list) -> FoundryProvider:
    c = ScriptedClient(replies)
    return FoundryProvider(endpoint="https://eval.invalid", api_key="eval", model="scripted-eval", client_factory=lambda: c)


def eval_until(m) -> int:
    head = headline_moment(detect(m, m.duration_seconds))
    return min(m.duration_seconds, head.detected_at + 120)


def run(smoke: bool) -> dict:
    ids = ["hcf-wva-tactical-shift"] if smoke else [x["match_id"] for x in list_matches()]
    results: dict[str, list[dict]] = {k: [] for k in (
        "turning_point_explanation", "numeric_grounding", "unsupported_event_rejection", "persona_style",
        "language_adherence", "recommendation_grounding", "agent_failure_fallback")}

    def rec(cat: str, name: str, ok: bool, detail: str = "") -> None:
        results[cat].append({"case": name, "pass": bool(ok), "detail": detail})

    for mid in ids:
        m = load_match(mid)
        until = eval_until(m)
        # 1. turning-point explanation
        s = run_pipeline(m, until, "analyst", "en", with_narrative=True)
        f = s.focus()
        n = s.narrative
        nums = {str(v) for k, v in f.params.items() if k in ("share_before", "share_after", "shots_before", "shots_after") and v is not None}
        text = n.headline + " " + n.explanation
        rec("turning_point_explanation", f"{mid}:{f.type}",
            m.team(f.team_id).name in text and all(x in text for x in nums) and f.evidence and f.before_state is not None,
            f"{f.type} @ {f.detected_at}s, numbers {sorted(nums)}")
        # 2. numeric grounding across personas x locales (templates)
        bad = []
        for p in PERSONAS:
            for loc in LOCALES:
                s2 = run_pipeline(m, until, p, loc, with_narrative=True)
                facts = nar.localise(nar.moment_facts(m, s2.focus()), loc)
                issues = EvidenceVerifierAgent.check_text(s2, [s2.narrative.headline, s2.narrative.explanation, *s2.narrative.bullets], facts)
                if issues:
                    bad.append(f"{p}/{loc}: {issues[:2]}")
        rec("numeric_grounding", f"{mid}:templates x12", not bad, "; ".join(bad) or "all numbers grounded")
        # 2b. adversarial LLM: invented number twice -> must end grounded (fallback)
        CACHE._d.clear()
        adv = json.dumps({"headline": "Huge swing", "explanation": "They now have 99% of the ball and 14 shots.", "bullets": []})
        s3 = run_pipeline(m, until, "analyst", "en", with_narrative=True, provider=fake([adv, adv]))
        rec("numeric_grounding", f"{mid}:adversarial_numbers", s3.narrative.source == "template" and "99" not in s3.narrative.explanation,
            f"final source={s3.narrative.source}")
        # 3. unsupported events / players
        s4 = run_pipeline(m, until)
        future = next((e.event_id for e in m.events if e.match_second > until), None)
        s4.observations = []
        s4.tactical = [Recommendation(id="fab-event", agent="eval", text="x", event_ids=["does-not-exist"]),
                       Recommendation(id="fab-player", agent="eval", text="x", player_ids=["XXX-99"])]
        if future:
            s4.tactical.append(Recommendation(id="future-event", agent="eval", text="x", event_ids=[future]))
        EvidenceVerifierAgent().run(s4)
        rec("unsupported_event_rejection", f"{mid}:fabricated", s4.verification.rejected == (3 if future else 2) and not s4.tactical,
            f"rejected={s4.verification.rejected}")
        CACHE._d.clear()
        ent = json.dumps({"headline": "Change", "explanation": "Roberto Fantasma changed everything.", "bullets": []})
        s5 = run_pipeline(m, until, "fan", "en", with_narrative=True, provider=fake([ent, ent]))
        rec("unsupported_event_rejection", f"{mid}:unknown_player_text", "Fantasma" not in s5.narrative.explanation, s5.narrative.source)
        # 4. persona style
        outs = {p: run_pipeline(m, until, p, "en", with_narrative=True).narrative for p in PERSONAS}
        rec("persona_style", f"{mid}:coach", any(b.startswith("For ") for b in outs["coach"].bullets))
        rec("persona_style", f"{mid}:analyst", any("Confidence" in b for b in outs["analyst"].bullets))
        rec("persona_style", f"{mid}:broadcaster", outs["broadcaster"].explanation.startswith("Talking point"))
        rec("persona_style", f"{mid}:fan", len(NUM_RE.findall(outs["fan"].explanation)) <= 1, outs["fan"].explanation)
        # 5. language adherence + invariance
        en = run_pipeline(m, until, "analyst", "en", with_narrative=True).narrative
        for loc in ("tr", "es"):
            o = run_pipeline(m, until, "analyst", loc, with_narrative=True).narrative
            stop = len(EN_STOP.findall(o.explanation))
            same_nums = sorted(NUM_RE.findall(o.explanation)) == sorted(NUM_RE.findall(en.explanation))
            rec("language_adherence", f"{mid}:{loc}", stop <= 1 and same_nums and o.explanation != en.explanation,
                f"english stopwords={stop}, numbers identical={same_nums}")
        # 6. recommendation grounding
        s6 = run_pipeline(m, until)
        recs = [c for c in s6.tactical if c.kind == "recommendation"]
        rec("recommendation_grounding", f"{mid}:recommendations", bool(recs) and all(c.verified and c.metrics for c in recs),
            f"{len(recs)} recommendations, all verified={all(c.verified for c in recs)}")
        # 7. agent failure fallback
        for agent in ("event_analyst", "tactical_analyst", "evidence_verifier", "narrative"):
            s7 = run_pipeline(m, until, with_narrative=True, fail={agent})
            t = {x.agent: x for x in s7.trace}
            others_ok = all(x.status in ("ok", "fallback") for k, x in t.items() if k != agent)
            ok = t[agent].status == "failed" and others_ok
            if agent == "narrative":
                ok = ok and s7.narrative is None and s7.focus().explanation_status == "unavailable"
            rec("agent_failure_fallback", f"{mid}:{agent}", ok)
        CACHE._d.clear()
        s8 = run_pipeline(m, until, with_narrative=True, provider=fake([TimeoutError("simulated"), TimeoutError("simulated")]))
        rec("agent_failure_fallback", f"{mid}:foundry_timeout", s8.narrative is not None and s8.narrative.source == "template")
    summary = {k: {"passed": sum(r["pass"] for r in v), "total": len(v)} for k, v in results.items()}
    return {"mode": "smoke" if smoke else "full", "matches": ids, "summary": summary, "results": results,
            "provider_note": "Offline evaluation: deterministic templates and scripted fake LLM replies. No Azure AI Foundry calls were made."}


def write(rep: dict) -> None:
    (OUT / "report.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = ["# Rely Match Brain - AI evaluation report", "",
             f"Mode: **{rep['mode']}**, matches: {', '.join(rep['matches'])}", "", f"> {rep['provider_note']}", "",
             "| Category | Passed | Total |", "|---|---|---|"]
    for k, v in rep["summary"].items():
        lines.append(f"| {k.replace('_', ' ')} | {v['passed']} | {v['total']} |")
    tp = sum(v["passed"] for v in rep["summary"].values())
    tt = sum(v["total"] for v in rep["summary"].values())
    lines += ["", f"**Overall: {tp}/{tt} cases passed.**", "", "## Cases", ""]
    for k, rs in rep["results"].items():
        lines.append(f"### {k.replace('_', ' ')}")
        for r in rs:
            lines.append(f"- {'PASS' if r['pass'] else 'FAIL'} `{r['case']}` {r['detail']}".rstrip())
        lines.append("")
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    rep = run(a.smoke)
    rep["seconds"] = round(time.time() - t0, 1)
    if not a.smoke:
        write(rep)
    tp = sum(v["passed"] for v in rep["summary"].values())
    tt = sum(v["total"] for v in rep["summary"].values())
    print(json.dumps(rep["summary"]))
    print(f"overall {tp}/{tt} in {rep['seconds']}s")
    return 0 if tp == tt else 1


if __name__ == "__main__":
    raise SystemExit(main())
