# Synthetic data

All data here is **synthetic**: fictional clubs, fictional players, simulated events. It is not derived from any real
match, league or provider.

- `schemas/event.schema.json`, `schemas/match.schema.json`: JSON Schemas exported from the API's pydantic models
  (`python -m scripts.export_schema` in `apps/api`). A test checks that they stay in sync.
- `scenarios/*.json`: scenario scripts (teams, phase parameters per team, scripted goals, substitutions, red cards,
  role changes, demo start). `teams.json` holds the four fictional squads.
- `generators/generate.py`: seeded possession-based simulator (Python standard library only). Possessions are built
  from passes, carries, dribbles, crosses, pressures, duels, tackles, interceptions, recoveries, fouls, cards, shots,
  goalkeeper actions, clearances, restarts, substitutions and possession changes.
- `generators/select_seeds.py`: scans seeds from each scenario's `base_seed` and keeps the first one whose match meets
  the scenario's acceptance criteria (story beats such as "the surge is detected before the equaliser") and realism
  bounds (8–22 shots and xG <= 3.6 per team, all scripted goals scored).
- `matches/*.json`: committed generated matches; `matches/index.json` lists them.

| Match | Scenario | Seed | Events | Goals (minute, team) |
|---|---|---|---|---|
| hcf-wva-tactical-shift | tactical_shift | 2028 | 2,504 | 32 WVA, 69 HCF, 83 HCF |
| kmr-elt-red-card | red_card | 10 | 2,420 | 13 ELT, 58 KMR, 74 KMR |
| wva-kmr-late-comeback | late_comeback | 93 | 2,551 | 23 KMR, 82 WVA, 89 WVA |
| elt-hcf-balanced | balanced | 11 | 2,599 | 40 ELT, 66 HCF |
| kmr-hcf-high-press | high_press | 303 | 2,703 | 17 KMR, 73 HCF |

Coordinates are 0–100 in the acting team's attacking frame: x = 100 is the goal they attack; y < 33.3 is their left
channel, 33.3–66.7 the centre and > 66.7 their right channel.
