// Captures the README screenshots and walks the scripted demo flow, reporting console errors.
// Usage: node scripts/screenshots.mjs [--url http://127.0.0.1:3100] [--size 1440x900] [--out ../../docs/screenshots]
// Requires the API (127.0.0.1:8100), the web app (production build recommended) and a local Chrome.
import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";

const arg = (k, d) => {
  const i = process.argv.indexOf(k);
  return i > -1 ? process.argv[i + 1] : d;
};
const BASE = arg("--url", "http://127.0.0.1:3100");
const [W, H] = arg("--size", "1440x900").split("x").map(Number);
const OUT = path.resolve(arg("--out", "../../docs/screenshots"));
const CHROME = arg("--chrome", "C:/Program Files/Google/Chrome/Application/chrome.exe");

fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ executablePath: CHROME });
const page = await (await browser.newContext({ viewport: { width: W, height: H } })).newPage();

const problems = [];
page.on("console", (m) => m.type() === "error" && problems.push(m.text().slice(0, 160)));
page.on("pageerror", (e) => problems.push(`pageerror: ${e.message.slice(0, 160)}`));
page.on("response", (r) => r.status() >= 400 && problems.push(`HTTP ${r.status()} ${r.url().slice(0, 140)}`));

const shot = (name) => page.screenshot({ path: path.join(OUT, `${name}.png`) });
const click = async (re) => {
  await page.getByRole("button", { name: re }).first().click();
  await page.waitForTimeout(700);
};

const started = Date.now();
await page.goto(`${BASE}/?demo=1`, { waitUntil: "networkidle" });
await page.waitForTimeout(800);
await shot("01-match-brain");
await click(/Jump to Turning Point/i);
await click(/Explain Moment/i);
await shot("02-turning-point");
await page.getByRole("button", { name: /^Evidence$/ }).first().click().catch(() => {});
await page.waitForTimeout(600);
await shot("03-evidence");
await page.selectOption('select[aria-label="persona"]', "coach");
await page.waitForTimeout(400);
await shot("04-persona-coach");
await page.selectOption('select[aria-label="persona"]', "broadcaster");
await page.waitForTimeout(400);
await shot("05-persona-broadcaster");
await click(/Generate Response|Generate Tactical Response/i);
await page.waitForTimeout(1200);
await shot("06-tactical-response");
await page.getByText(/^Agent Trace$/).first().click().catch(() => {});
await page.waitForTimeout(600);
await shot("07-agent-trace");
await click(/Generate Recap|Recap/i);
await shot("08-recap-en");
await page.selectOption('select[aria-label="language"]', "tr");
await page.waitForTimeout(700);
await shot("09-recap-tr");
await page.selectOption('select[aria-label="language"]', "es");
await page.waitForTimeout(700);
await shot("10-recap-es");

console.log(`captured ${OUT} in ${((Date.now() - started) / 1000).toFixed(1)} s`);
console.log(problems.length ? `console or network problems:\n${[...new Set(problems)].join("\n")}` : "no console or network errors");
await browser.close();
