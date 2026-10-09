# Video shot list (measured 1:48)

Shot-by-shot companion to [DEMO_SCRIPT.md](DEMO_SCRIPT.md). Same times, same narration. Times come from a scripted
run of this sequence on the production build, with real playback and narration-length holds; re-time your own take.

| # | Time | Page / state | Mouse action | Narration | Important visual |
|---|---|---|---|---|---|
| 1 | 0:00–0:08 | `/?demo=1`, kick-off | None. Cursor parked off the controls | "Football changes before the scoreboard does. Rely Match Brain turns synthetic match events into explainable intelligence in real time." | Scoreboard, **SYNTHETIC FOOTBALL-REALISTIC DATA** label, explanatory line above the feed |
| 2 | 0:08–0:39 | Playback at 20x from 50:00 | Click **Play Demo**, then hands off | "The match is reconstructed only from events received so far. Nothing is precomputed from the final result." | Clock running, numbered arrows on the pitch, feed filling, momentum line |
| 3 | 0:39–0:46 | Banner **Turning point detected** (match clock 60:03) | None | "After this substitution, Rely detects a major change in how the team progresses down the right side." | Orange banner |
| 4 | 0:46–0:56 | **Why did the match change?** | Click the banner | "Before the change, 25 percent of progressive actions came from the right channel. At detection, that rises to 71 percent." | **SUBSTITUTION IMPACT** chip, Before 5/20 (25%), Trigger 56:03, After 5/7 (71%) |
| 5 | 0:56–1:04 | **Evidence** tab | Click **Evidence** | "Every number is recomputed from the synthetic event stream. Rely separates verified evidence from causal hypotheses." | Coverage bar: 20 supported · 2 unverifiable (causal) · 0 rejected; event id and windows |
| 6 | 1:04–1:09 | Why tab, persona **Coach** → **Broadcaster** | Click **Why did the match change?**; choose **Coach**, then **Broadcaster** in the persona selector | "The same evidence becomes different intelligence depending on who is using it." | Coach: per-team decisions. Broadcaster: talking point. Same numbers |
| 7 | 1:09–1:20 | Tactical response | Click **Generate Response** | "Rely can turn the finding into a tactical response, while showing the trade-off instead of pretending there is one correct answer." | 4-3-3 → 3-2-5 preview with arrows, player movements, trade-off / risk box, suggested-response line |
| 8 | 1:20–1:33 | **Agent Trace** | Click **Agent Trace** | "Specialized agents analyse events, interpret tactics, verify evidence and create the narrative through structured handoffs. The architecture is ready for Microsoft Foundry, while this demo uses the local fallback." | Per-agent status and ms; narrative provider shown as none / template |
| 9 | 1:33–1:41 | Recap, EN → TR → ES | Click **Generate Recap**; choose **TR**, wait about 3 s, choose **ES** | "The facts stay the same. Only the experience changes." | Same score and minutes in three languages |
| 10 | 1:41–1:48 | Closing card | Cut to [video/closing-card.png](video/closing-card.png) in the editor | "Rely Match Brain. From football events to understanding. From understanding to decisions." | Title, tagline, pitch with the turning-point arrow |

## Before you press record

- Production build only; no Next.js dev badge.
- No console, bookmarks bar or extension icons; hide the address bar if you can.
- 1920×1080 preferred, 1440×900 acceptable; browser zoom 100% so text survives YouTube compression.
- Reload `/?demo=1` so the take starts at kick-off, with the API already warm.
- No visible internal ids beyond the short event ids recording mode shows.
- Voice only. No music, broadcast footage or third-party logos. The clubs are fictional.
