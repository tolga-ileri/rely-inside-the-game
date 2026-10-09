# Demo script: Rely Match Brain (measured 1:48)

Final narration for the submission video. It matches [VIDEO_SHOT_LIST.md](VIDEO_SHOT_LIST.md) shot for shot.

**How the 1:48 was measured.** A scripted browser run of exactly this sequence on the production build: it clicked the
same controls, waited for the real playback to reach the turning point, and held every screen for as long as its
narration takes to speak at about 150 words per minute, plus short pauses. Play Demo to the turning-point banner took
**31.0 s** of real playback. A person reading at a different pace will land a few seconds either side; time your own
take before submitting and stay under 1:55.

Recording: production build, `http://127.0.0.1:3100/?demo=1`, API with `AI_PROVIDER=none`. Voice only, no music.

| Time | On screen | Say |
|---|---|---|
| 0:00 | Opening screen: scoreboard, pitch, synthetic-data label | "Football changes before the scoreboard does. Rely Match Brain turns synthetic match events into explainable intelligence in real time." |
| 0:08 | Click **Play Demo**. Events stream: clock, pitch arrows, intelligence feed | "The match is reconstructed only from events received so far. Nothing is precomputed from the final result." Then let the match play; no talking needed until the banner. |
| 0:39 | **Turning point detected** banner, then the **SUBSTITUTION IMPACT** chip | "After this substitution, Rely detects a major change in how the team progresses down the right side." |
| 0:46 | Click the banner. **Why did the match change?**: Before, Trigger, After | "Before the change, 25 percent of progressive actions came from the right channel. At detection, that rises to 71 percent." |
| 0:56 | **Evidence** tab: 20 supported, 2 unverifiable, 0 rejected | "Every number is recomputed from the synthetic event stream. Rely separates verified evidence from causal hypotheses." |
| 1:04 | Back to **Why**. Persona: **Coach**, then **Broadcaster** | "The same evidence becomes different intelligence depending on who is using it." |
| 1:09 | **Generate Response**: 4-3-3 → 3-2-5 preview, movements, trade-off / risk | "Rely can turn the finding into a tactical response, while showing the trade-off instead of pretending there is one correct answer." |
| 1:20 | **Agent Trace** tab | "Specialized agents analyse events, interpret tactics, verify evidence and create the narrative through structured handoffs. The architecture is ready for Microsoft Foundry, while this demo uses the local fallback." |
| 1:33 | **Generate Recap**, then language **TR**, then **ES** | "The facts stay the same. Only the experience changes." |
| 1:41 | Closing card ([video/closing-card.png](video/closing-card.png)) | "Rely Match Brain. From football events to understanding. From understanding to decisions." |
| 1:48 | End | |

Two rules for the narration:

- At 0:46 say **71 percent at detection**. The 75 percent figure is the complete six-minute window (9 of 12 actions),
  which includes events after detection. Only mention it if you explain that difference.
- Do not say the demo runs on Microsoft Foundry unless you have configured it and the Agent Trace shows
  `microsoft_foundry` for the narrative agent. See [FOUNDRY_SETUP.md](FOUNDRY_SETUP.md).

## Recording checklist

- Production build only (`pnpm build`, then `pnpm start -p 3100`). The dev server shows a Next.js badge.
- Browser: no console, no bookmarks bar, no extensions toolbar; ideally a kiosk or app window without the address bar.
- Record at 1920×1080 if your recorder supports it, otherwise 1440×900. Browser zoom 100%.
- Open `/?demo=1` once before recording to warm the API; then reload so the take starts at kick-off.
- Park the cursor off the controls between clicks so no tooltip opens.
- Voice only. No music, broadcast footage or third-party logos.
- If anything goes wrong mid-take, **Jump to Turning Point** recovers the flow.
- Optional, not in the video: `/?fail=narrative` shows the structured intelligence with "AI explanation unavailable".
