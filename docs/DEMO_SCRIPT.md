# Demo script (target 1:45–1:55)

Record at 1440×900 using `http://127.0.0.1:3100/?demo=1`. Recording mode is deterministic, shows no debug counters,
and shortens internal ids. The API runs with `AI_PROVIDER=none` unless Foundry credentials are configured. If they are,
say "Foundry" only when the Agent Trace shows `microsoft_foundry`.

Measured on the build machine with `apps/web/scripts/screenshots.mjs`: the turning-point banner appears
**31.2 s** after pressing *Play Demo* (detected at match clock 60:03; playback starts at 50:00 at 20x).
Every click below responds in under 1 s locally.

| Time | Screen / action | Voice-over (suggested) |
|---|---|---|
| 0:00–0:08 | App open on `/`: scoreboard, **SYNTHETIC FOOTBALL-REALISTIC DATA** label | "This is Rely Match Brain. It turns football events into understanding, and understanding into decisions. Everything here is synthetic data." |
| 0:08–0:12 | Click **Play Demo** | "We replay a match at 20 times speed. The system only sees events up to the current second." |
| 0:12–0:43 | Live playback: sequence viewer with numbered arrows, intelligence feed, channel bars, momentum timeline. At ~0:43 the **Turning point detected · 60:03** banner appears and playback pauses | "The match state updates with every event: possession, entries by channel, pressures, momentum. Rules, not AI, decide when the match has changed. Here: Harbour City's 56th-minute substitution moved their attack to the right." |
| 0:43–1:03 | Click the banner (**Explain Moment**). Show **Before / Trigger / After**, then the **Evidence** tab | "Before the change, 25% of their progressive actions went down the right. After it, 75%. Every number links to event ids, timestamps and windows, and the verifier re-checks every claim. Coverage is 91%, not a fake 100%, because causal hypotheses stay marked as unverifiable." |
| 1:03–1:18 | Back to **Why**, persona lens: **Coach** → **Broadcaster** → **Fan**; then **Switch Language** (TR, ES) | "Same evidence, different presentation: instructions for the coach, a talking point for the broadcaster, plain words for the fan. Switching language changes the words only. The numbers stay the same." |
| 1:18–1:35 | Back to EN. **Generate Response**: the Studio preview animates 4-3-3 → 3-2-5; click **counter 5 4 1** for what-if | "Rely turns understanding into a decision: amplify the shift with a 3-2-5. The right-back inverts, the left-back pushes high, a midfielder attacks the half-space, the winger holds the width. The risk is stated. What-if never predicts a score." |
| 1:35–1:45 | **Agent Trace** tab | "Six stages with per-agent latency, provider and fallback status. If an agent fails, the others still deliver." |
| 1:45–1:52 | **Generate Recap**: 30-second recap, switch to Turkish 2-minute analyst | "At full time, recaps for every audience and language, built only from evidence." |
| 1:52–1:55 | Hold on the recap | "Rely Match Brain: from football events to understanding, from understanding to decisions." |

Total: about **1:55**. To shorten to 1:45, skip the Fan persona and the Spanish recap.

## Rehearsal checklist

- `GET http://127.0.0.1:8100/ready` returns `ready: true`.
- Open `/?demo=1` once before recording to warm up the API cache (first `/live` call is about 200 ms).
- Do not seek on the timeline during the recording. *Jump to Turning Point* is the fallback if something goes wrong.
- Optional recovery demo (not recorded): `/?fail=narrative` shows "AI explanation unavailable" with the structured intelligence still in place.
