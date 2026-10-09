// Captures the README screenshots at 1440x900 and times the scripted demo flow.
// Usage: node scripts/screenshots.mjs [--url http://127.0.0.1:3100] [--size 1440x900] [--out ../../docs/screenshots]
// Requires the API (127.0.0.1:8100) and web (127.0.0.1:3100) to be running, and a local Chrome.
import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";

const arg = (k, d) => {
  const i = process.argv.indexOf(k);
  return i > -1 ? process.argv[i + 1] : d;
};
const URL = arg("--url", "http://127.0.0.1:3100");
const [W, H] = arg("--size", "1440x900").split("x").map(Number);
const OUT = path.resolve(arg("--out", "../../docs/screenshots"));
const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const prefix = W === 1440 ? "" : `${W}x${H}-`;
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const shot = async (name) => {
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(OUT, `${prefix}${name}.png`) });
  console.log("saved", `${prefix}${name}.png`);
};
const timings = {};
const t0 = Date.now();
const mark = (k) => (timings[k] = +((Date.now() - t0) / 1000).toFixed(1));

await page.goto(`${URL}/?demo=1`, { waitUntil: "networkidle" });
await page.getByTestId("scoreboard").waitFor();
mark("page_ready");

// 1. Play Demo -> live hero shot, then the turning point banner.
const playAt = Date.now();
await page.getByRole("button", { name: /Play Demo/ }).click();
await page.waitForTimeout(14000);
await shot("01-hero-live");
await page.getByTestId("banner").waitFor({ timeout: 60000 });
timings.turning_point_after_play_s = +((Date.now() - playAt) / 1000).toFixed(1);
mark("turning_point");
await shot("02-turning-point");

// 2. Explain Moment -> Why did the match change?
await page.getByTestId("banner").click();
await page.getByTestId("why-panel").waitFor();
mark("explained");
await shot("03-why-moment");

// 3. Evidence panel
await page.getByRole("button", { name: "Evidence", exact: true }).click();
await page.getByTestId("evidence-panel").waitFor();
await shot("04-evidence");

// 4. Persona lens: coach, then broadcaster
await page.getByRole("button", { name: "Why did the match change?", exact: true }).click();
await page.getByTestId("persona-lens").getByRole("button", { name: "Coach" }).click();
await page.waitForTimeout(700);
await shot("05-persona-coach");
await page.getByTestId("persona-lens").getByRole("button", { name: "Broadcaster" }).click();
await page.waitForTimeout(700);
await shot("05b-persona-broadcaster");
mark("persona");

// 5. Tactical response (Studio preview animates 4-3-3 -> 3-2-5) + what-if
await page.getByRole("button", { name: "Generate Response" }).click();
await page.getByTestId("tactical-panel").waitFor();
await page.waitForTimeout(2600);
await shot("06-tactical-response");
await page.getByRole("button", { name: "counter 5 4 1" }).click();
await page.getByTestId("whatif").waitFor();
await page.getByTestId("whatif").scrollIntoViewIfNeeded();
await shot("06b-what-if");
mark("response");

// 6. Agent trace
await page.getByRole("button", { name: "Agent Trace", exact: true }).click();
await page.getByTestId("trace-panel").waitFor();
await shot("07-agent-trace");

// 7. Recap, multilingual
await page.getByRole("button", { name: "Generate Recap" }).click();
await page.getByTestId("recap-panel").waitFor();
await page.getByRole("button", { name: "Switch Language" }).click(); // EN -> TR
await page.waitForTimeout(900);
await page.getByRole("button", { name: "2 dk analist" }).click();
await page.waitForTimeout(400);
await shot("08-recap-tr");
await page.getByRole("button", { name: "Dil Değiştir" }).click(); // TR -> ES
await page.waitForTimeout(900);
await shot("09-recap-es");
mark("recap");

await browser.close();
fs.writeFileSync(path.join(OUT, `${prefix}timings.json`), JSON.stringify(timings, null, 1));
console.log(JSON.stringify(timings));
