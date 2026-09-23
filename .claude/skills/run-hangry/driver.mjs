#!/usr/bin/env node
// Minimal chromium-cli-style REPL for driving the Hangry client, since no
// chromium-cli binary is available in this environment. Reads one command
// per line from stdin, drives a single headless Chromium page via
// Playwright, writes screenshots next to this file.
//
// Commands:
//   nav <url>
//   wait-for text=<substring>          (waits up to 10s)
//   wait-for <css-selector>
//   click <css-selector>
//   fill <css-selector> <value...>
//   press <key>                         (e.g. Enter)
//   screenshot [name]                   (default: shot-<n>.png)
//   console                             (dump collected console messages)
//   console --errors                    (dump only page errors / console.error)
//   eval <js-expression>                (page.evaluate, prints the result)
//   sleep <ms>                          (fixed wait — only for an async
//                                        effect with no DOM signal to poll,
//                                        e.g. a console error after a click)
//   quit
//
// Usage:
//   node driver.mjs <<'EOF'
//   nav http://localhost:5173
//   wait-for text=Hangry
//   screenshot home
//   EOF

import { chromium } from "playwright";
import { createInterface } from "node:readline";
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const SKILL_DIR = dirname(fileURLToPath(import.meta.url));
const SHOTS_DIR = join(SKILL_DIR, "screenshots");
mkdirSync(SHOTS_DIR, { recursive: true });

const consoleLog = [];
let shotCount = 0;

const browser = await chromium.launch();
const page = await browser.newPage();
page.on("console", (msg) => consoleLog.push({ type: msg.type(), text: msg.text() }));
page.on("pageerror", (err) => consoleLog.push({ type: "pageerror", text: String(err) }));

function log(...args) {
  console.log(...args);
}

async function runLine(line) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("#")) return;
  const [cmd, ...rest] = trimmed.split(" ");
  const arg = rest.join(" ");

  try {
    switch (cmd) {
      case "nav": {
        await page.goto(arg, { waitUntil: "domcontentloaded" });
        log(`[nav] ${arg} -> ${page.url()}`);
        break;
      }
      case "wait-for": {
        if (arg.startsWith("text=")) {
          await page.getByText(arg.slice(5), { exact: false }).first().waitFor({ timeout: 10000 });
        } else {
          await page.waitForSelector(arg, { timeout: 10000 });
        }
        log(`[wait-for] ok: ${arg}`);
        break;
      }
      case "click": {
        await page.click(arg, { timeout: 10000 });
        log(`[click] ok: ${arg}`);
        break;
      }
      case "fill": {
        // No value (`fill <selector>`) clears the field.
        const sp = arg.indexOf(" ");
        const sel = sp === -1 ? arg : arg.slice(0, sp);
        const value = sp === -1 ? "" : arg.slice(sp + 1);
        await page.fill(sel, value, { timeout: 10000 });
        log(`[fill] ${sel} = ${value}`);
        break;
      }
      case "press": {
        await page.keyboard.press(arg);
        log(`[press] ${arg}`);
        break;
      }
      case "screenshot": {
        shotCount += 1;
        const name = arg || `shot-${shotCount}`;
        const path = join(SHOTS_DIR, `${name}.png`);
        await page.screenshot({ path, fullPage: true });
        log(`[screenshot] ${path}`);
        break;
      }
      case "console": {
        const errorsOnly = arg.trim() === "--errors";
        const rows = errorsOnly
          ? consoleLog.filter((m) => m.type === "error" || m.type === "pageerror")
          : consoleLog;
        if (rows.length === 0) log("[console] (none)");
        for (const m of rows) log(`[console:${m.type}] ${m.text}`);
        break;
      }
      case "eval": {
        const result = await page.evaluate(arg);
        log("[eval]", result);
        break;
      }
      case "sleep": {
        const ms = Number(arg) || 0;
        await new Promise((resolve) => setTimeout(resolve, ms));
        log(`[sleep] ${ms}ms`);
        break;
      }
      case "quit":
      case "exit": {
        await browser.close();
        process.exit(0);
      }
      default:
        log(`[error] unknown command: ${cmd}`);
    }
  } catch (err) {
    log(`[error] ${cmd} ${arg} -> ${err.message}`);
  }
}

// Commands must run strictly in order (each drives the same page). Using
// readline's async iterator processes one line fully before pulling the
// next, even though stdin (a heredoc/pipe) delivers all lines at once.
const rl = createInterface({ input: process.stdin });
for await (const line of rl) {
  await runLine(line);
}
await browser.close();
process.exit(0);
