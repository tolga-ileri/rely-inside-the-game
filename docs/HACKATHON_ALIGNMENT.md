# Hackathon alignment: Inside the Game (Microsoft + Premier League)

## Judging criteria

| Judging category | Rely capability | Where |
|---|---|---|
| Technological Implementation | Deterministic event engine with rolling windows and no-future-leak tests; rule-based turning-point detector; typed schemas; 94 backend tests, 11 frontend tests, 100-case offline AI evaluation; CI with Docker builds and a secret scan | `apps/api/rely_brain/`, `apps/api/tests`, `apps/web/tests`, `apps/api/evals`, `.github/workflows/ci.yml` |
| Agentic Design & Innovation | Event Analyst, Tactical Analyst, Evidence Verifier and Narrative agent over one typed shared state, with structured handoffs, a verifier that can reject other agents' claims, and per-agent failure recovery | `apps/api/rely_brain/agents/`, `orchestrator.py` |
| Real-World Impact | One verified finding becomes a coach decision, analyst evidence, a broadcast talking point and a fan explanation; tactical responses state their trade-off | `narrative.py`, `tactics.py`, Why and Tactical panels |
| UX & Presentation | One screen: scoreboard, numbered pitch sequences, quiet feed, momentum timeline; Why / Evidence / Agent Trace / Tactical Response / Recap in a drawer; persona and language switch without recomputing facts | `apps/web/src/components/` |
| Challenge Adherence | Synthetic, football-realistic data only, labelled on every screen; explainable intelligence, real-time narratives, automated recaps, personalised experiences | `synthetic-data/`, UI label |

## Awards

| Award | Why Rely is relevant | Honest limit |
|---|---|---|
| Grand Prize | Not a summariser: events → deterministic intelligence → evidence verification → multi-agent reasoning → personalised narrative → tactical action | Demo data is synthetic by design |
| Best Use of Microsoft Foundry | Foundry provider for the Narrative agent with structured output, streaming, caching and a grounded fallback; setup path in [FOUNDRY_SETUP.md](FOUNDRY_SETUP.md) | No real Foundry call has been verified; the demo runs on the local fallback |
| Best Enterprise Solution | Typed contracts, deterministic core, evidence traceability, fallback, Agent Trace and structured logs, containers, CI | Not deployed |
| Best Multi-Agent Orchestration | Four agents with distinct roles, shared typed state, verifier with veto, failure recovery covered by evals | Three agents are deterministic code; only the Narrative agent uses a language model |
| Best Azure Cloud Native Integration | Dockerfiles, `/health` and `/ready`, Bicep template and deploy script for Azure Container Apps with probes and Log Analytics | Deployment-ready for Azure Container Apps; not deployed, and the Bicep template has not been compiled in CI |

Eligibility for any award is decided by the challenge rules and judges; this table only maps capabilities.

## What is real vs. planned

- **Real and tested:** synthetic data generator, match state, turning-point detector, agents, verifier, templates in three
  languages, API, UI, Docker images, evals.
- **Implemented, not exercised live:** Microsoft Foundry calls (no credentials; covered by stand-in tests) and the Azure
  Container Apps deployment (template and script written; deployment-ready, not deployed).
