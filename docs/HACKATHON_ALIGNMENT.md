# Hackathon alignment: Inside the Game (Microsoft + Premier League)

| Judging theme | How Rely Match Brain addresses it | Where |
|---|---|---|
| Deeper understanding of the game | Answers "Why did the match change?" while the match is live, with Before / Trigger / After windows built from events | `apps/api/rely_brain/turning_points.py`, Why panel |
| Use of AI / agents | Event Analyst, Tactical Analyst, Evidence Verifier and Narrative agents with explicit shared state, an orchestrator and per-agent recovery | `apps/api/rely_brain/agents/`, `orchestrator.py` |
| Microsoft technology | Azure AI Foundry provider (azure-ai-inference, JSON outputs, streaming), Azure Container Apps + ACR + Log Analytics templates, GitHub Actions | `rely_brain/llm.py`, `infra/azure/`, `.github/workflows/ci.yml` |
| Responsible AI | Rules decide facts; AI only phrases them. Numeric grounding, entity validation, honest evidence coverage, template fallback, no prompts or secrets in the UI | `rely_brain/guard.py`, `agents/verifier.py`, evals |
| Multiple audiences | Coach / Analyst / Broadcaster / Fan persona lens; EN / TR / ES; six recap formats; broadcast story cards and commentator prep | `narrative.py`, `i18n.py` |
| Fan experience | Plain-language fan view, social recap, live intelligence feed without spam (clustered moments) | UI feed, recaps |
| Decision support | Tactical Response with a Studio-style animated preview (4-3-3 → 3-2-5) and what-if (effect, advantage, risk, players, limitations; no score prediction) | `rely_brain/tactics.py`, Tactical panel |
| Technical quality | 88 backend tests (including no-future-leak tests), 11 frontend tests, 85-case AI eval suite, typed schemas, CI with gitleaks | `apps/api/tests`, `apps/web/tests`, `apps/api/evals` |
| Data compliance | 100% synthetic, seeded, reproducible data; fictional clubs; no real league data, logos or trademarks | `synthetic-data/` |

## What is real vs. planned

- **Real and tested:** synthetic data generator, match state, turning-point detector, agents, verifier, templates in three
  languages, API, UI, Docker images (both built and smoke-tested locally), evals.
- **Implemented, not yet exercised live:** Azure AI Foundry calls (no credentials on the build machine; covered by fake-client
  tests) and Azure Container Apps deployment (template and script written; not deployed).
