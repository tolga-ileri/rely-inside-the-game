# Video shot list (1:55 planned)

Record at 1440×900 from the production build: `http://127.0.0.1:3100/?demo=1`, with the API on `127.0.0.1:8100`
and `AI_PROVIDER=none`. Before recording: move the mouse off the controls, close other tabs, and hide any browser
toolbar that shows localhost URLs. Timings are planned durations. They are not a stopwatch run; re-time the
recording before submitting. See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the narration.

| # | Time | Page / state | Mouse action | Narration (suggested) | Important visual |
|---|---|---|---|---|---|
| 1 | 0:00–0:08 | `/?demo=1`, kick-off | none, cursor parked off-screen | "This is Rely Match Brain. It turns football events into understanding, and understanding into decisions." | Scoreboard, **SYNTHETIC FOOTBALL-REALISTIC DATA** label, the explanatory line at the top of the feed |
| 2 | 0:08–0:12 | Same | Click **Play Demo** | "We replay a match at twenty times speed. The system sees only events up to the current second." | Playback starts, clock moves |
| 3 | 0:12–0:43 | Live playback | none (let it run) | "Rules decide when the match has changed. Not AI." | Sequence viewer arrows, intelligence feed filling, momentum timeline |
| 4 | 0:43–0:50 | Turning-point banner at 60:03 | Click the banner or **Explain Moment** | "Here, Harbour City's 56th-minute substitution moves the attack to the right." | **SUBSTITUTION IMPACT** chip, the "HIGH" severity badge |
| 5 | 0:50–1:03 | Why panel | Hover the **Evidence** tab, then click it | "Before the change, 25% of progressive actions went down the right. At detection, 71%. Every number links to events and windows." | Before / Trigger / After cards; Evidence tab with event ids and windows |
| 6 | 1:03–1:10 | Evidence panel | none | "Coverage is 91%, not a fake 100%. The two unverifiable claims are causal hypotheses." | Coverage bar with its breakdown line |
| 7 | 1:10–1:15 | Why panel → **Coach** | Click the **Why** tab, then choose **Coach** in the persona selector | "The coach gets a decision." | Coach bullets per team; same numbers |
| 8 | 1:15–1:20 | **Broadcaster** | Choose **Broadcaster** | "The broadcaster gets a story. Same evidence." | Talking-point text |
| 9 | 1:20–1:28 | Tactical response | Click **Generate Response** | "Amplify with a 3-2-5. The right-back inverts, the left-back pushes high, the winger holds the width. The trade-off is stated." | 4-3-3 → 3-2-5 preview with arrows; trade-off / risk box; suggested-response disclaimer |
| 10 | 1:28–1:40 | Agent Trace tab | Click **Agent Trace** | "Each agent reports its status, latency and provider. If one fails, the others still deliver." | Table with per-agent ms, provider and fallback; narrative shown as local fallback |
| 11 | 1:40–1:46 | Recap, English | Click **Generate Recap** | "At full time, recaps for each audience." | 30-second recap text |
| 12 | 1:46–1:52 | Language switch to Turkish, then Spanish | Choose **TR**, then **ES** in the language selector | "The words change. The facts do not." | Turkish and Spanish recap text, same score and minutes |
| 13 | 1:52–1:55 | Hold on the recap | none | "Rely Match Brain: from football events to understanding, from understanding to decisions." | Final frame: recap with the synthetic-data label visible |

## Recording rules

- No browser console, dev overlay or localhost-looking debug UI: use the production build (`pnpm build`, then
  `pnpm start -p 3100`).
- No visible internal ids beyond the shortened ones the recording mode shows.
- No music, no broadcast footage, no third-party logos. The clubs are fictional and use Rely's own crest style.
- Do not seek on the timeline during the take. **Jump to Turning Point** is the fallback.
