# Architecture

```
apps/api/rely_brain/
  schemas.py          typed Event, Match, MatchState, WindowMetrics, MatchMoment, Claim types, AgentTrace
  data.py             loads synthetic matches; events_until(match, t) is the only event accessor
  windows.py          metric definitions + window_metrics(start, end) + before_after (truncated at `until`)
  state.py            Match State engine (score, possession, entries by channel, momentum, sequences, involvement)
  turning_points.py   deterministic detector (rules + thresholds documented in the module docstring)
  agents/             base (SharedState), event_analyst, tactical_analyst, verifier, narrative_agent
  orchestrator.py     runs the pipeline with per-agent recovery and tracing
  narrative.py        persona x locale templates, feed, story chapters, broadcast cards, recaps
  i18n.py             EN / TR / ES strings
  guard.py            numeric grounding + entity validation
  llm.py              AI provider abstraction (none | microsoft_foundry), response cache
  tactics.py          Tactical Response (formations, movements) + what-if
  api.py              FastAPI endpoints; logging_setup.py: JSON logs
apps/web/src/
  lib/playback.ts     pure playback reducer (play/pause/speed/seek/tick)
  lib/api.ts, types.ts, i18n.ts
  components/         MatchBrainApp, Pitch (sequence viewer), Timeline, Feed, Controls, Panels (Why/Evidence/Trace/Tactics/Recap)
```

## Data flow per request

1. The client clock `t` advances (1x / 5x / 20x match-seconds per second). The client calls `GET /live?until=t`
   roughly every 10 match seconds at 20x.
2. `compute_state(match, t)` uses only `events_until(match, t)`.
3. `detect(match, t)` evaluates rolling rules at minute cuts `<= t`; event rules (red card, goal, substitution) fire
   when their event arrives. After windows are truncated at `t` and flagged `after_window_complete=false`.
4. Agents run over the shared state; `GET /explain` also runs the Narrative agent for one moment.

## Turning-point rules

| Rule | Condition (defaults in `TH`) |
|---|---|
| sub_shift | substitution, then 4–10' later a channel's share of the team's progressive actions rises >= 30 points to >= 55% (>= 6 actions) |
| red_card | every red card; opponent pass share, territory and entries plus the team's high pressures, before vs after |
| shot_surge | >= 5 shots in the last 10' and >= previous 10' + 4 |
| momentum_swing | mean momentum (last 5' vs previous 5') moves >= 55 towards a team, new mean >= 30 |
| channel_dominance | >= 8 final-third entries in 10', >= 60% through one channel (previous < 40%) |
| possession_swing | pass share +20 points between consecutive 10' windows (>= 35 passes each) |
| dangerous_sequences | >= 5 box-reaching or shot-ending sequences in 8', previous 8' <= 1 |

Rolling moments of the same team detected within 10' of an earlier moment are merged into it as supporting rules,
which keeps the feed compact.

## Momentum

Per minute and per team, a threat score is computed: final-third entry 1, box entry 2, shot 3, high pressure 0.5,
recovery in the opponent half 0.5. Momentum is the EWMA (alpha 0.25) of home minus away, squashed with `tanh` to
-100..100.

## Grounding and verification

- Claims carry metric paths (`state.last10.HCF.shots`, `moment.<id>.after.prog_share_R`, `window.HCF.3000.3600.shots`).
  The verifier recomputes each one from raw events at or before `until`, checks that event ids exist and are not in the
  future, that players are in the roster and that timestamps are at or before `until`.
- Generated text: every number must appear in the moment facts (formation names such as 4-3-3 are vocabulary).
  Capitalised multi-word names must be known players or teams.
- Evidence coverage = supported / total claims. Hypotheses count as unverifiable.

## No-future-leak guarantee

`tests/test_no_future_leak.py` compares state and detection on the full match vs. a physically truncated match for
many cut-offs. It also asserts that no moment, evidence item or claim references an event after `until`, and that
changing every future event does not change the past state.
