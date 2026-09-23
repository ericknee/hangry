---
name: run-hangry
description: Build, run, and drive Hangry (the FastAPI + LangGraph service and its React client). Use when asked to start Hangry, run its tests, build it, take a screenshot of its UI, or interact with the running app.
---

Hangry is a FastAPI service (`packages/api`, backed by a LangGraph agent in
`packages/agent`) plus a separate React/Vite client (`client/`). Drive it by
starting both dev servers and then scripting a headless Chromium page via
`.claude/skills/run-hangry/driver.mjs` (no `chromium-cli` binary is available
in this environment, so this driver stands in for it — same idea, its own
small command set). All paths below are relative to the repo root.

## Prerequisites

Verified on Windows with Git Bash as the shell (`uv`, `node`/`npm`, and
`python` already on `PATH` — no OS packages needed):

```bash
uv --version      # 0.8.13+
node --version    # v24+
npm --version     # 11+
```

## Setup

```bash
uv sync --all-packages          # installs packages/agent + packages/api into .venv
cd client && npm install && cd ..
cd .claude/skills/run-hangry && npm install && cd ../../..   # installs the driver's playwright dep
npx --prefix .claude/skills/run-hangry playwright install chromium   # downloads the matching browser build
```

No `.env` is required to run what's described below. `packages/api/src/api/core/config.py`
requires `database_url`, `anthropic_api_key`, and `google_places_api_key` —
but nothing on the request path used here (`GET /health`, `POST /sessions`)
imports `api/db/database.py` or calls `get_settings()`, so the server starts
and serves those routes with no env file at all. You'd only need a real
`.env` (Postgres up via `docker compose up -d`, plus real API keys) to
exercise code paths that aren't wired yet — see Gotchas.

## Build

No build step needed to run in dev mode (see below). `cd client && npm run build`
exists (`tsc -b && vite build`) if you need a production client bundle, but
running the app doesn't require it.

## Run (agent path)

Start both dev servers in the background, then drive the client through
`driver.mjs`.

```bash
# 1. API — port 8000
uv run uvicorn api.main:app --app-dir packages/api/src --port 8000 > /tmp/api.log 2>&1 &
timeout 15 bash -c 'until curl -sf http://localhost:8000/health >/dev/null; do sleep 0.5; done'

# 2. Client — port 5173, proxies /api/* to :8000 (see Gotchas — the prefix doesn't match)
(cd client && npm run dev > /tmp/client.log 2>&1 &)
timeout 15 bash -c 'until curl -sf http://localhost:5173/ >/dev/null; do sleep 0.5; done'
```

Drive it — `driver.mjs` reads one command per line from stdin against a
single headless Chromium page:

```bash
node .claude/skills/run-hangry/driver.mjs <<'EOF'
nav http://localhost:5173
wait-for text=Hangry
screenshot 01-home
fill input tacos
click button:has-text("Just me")
sleep 500
console --errors
quit
EOF
```

Screenshots land in `.claude/skills/run-hangry/screenshots/`. That command
sequence is the real "create a solo session" flow — see Gotchas, it
currently fails partway (the button click doesn't navigate) and that's
expected, not a driver bug. To see the elicitation/shortlist pages render,
get a session id directly from the API and navigate straight there:

```bash
SID=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"mode":"solo","initial_query":"tacos"}' \
  | node -e "process.stdin.on('data', d => console.log(JSON.parse(d).session_id))")

node .claude/skills/run-hangry/driver.mjs <<EOF
nav http://localhost:5173/session/$SID
wait-for text=How far are you willing to travel
screenshot 02-elicitation
click button:has-text("15 min")
nav http://localhost:5173/session/$SID/shortlist
wait-for text=Your shortlist
screenshot 03-shortlist
quit
EOF
```

Driver commands:

| command | what it does |
|---|---|
| `nav <url>` | navigate the page |
| `wait-for text=<substring>` | wait up to 10s for text to appear |
| `wait-for <css-selector>` | wait up to 10s for a selector |
| `click <css-selector>` | click (selectors with spaces need to be simple — see Gotchas) |
| `fill <css-selector> <value...>` | fill an input |
| `press <key>` | keyboard press, e.g. `Enter` |
| `screenshot [name]` | full-page PNG to `screenshots/<name>.png` |
| `console` / `console --errors` | dump collected browser console messages |
| `eval <js>` | `page.evaluate`, prints the result |
| `sleep <ms>` | fixed wait — only when there's no DOM signal to poll for (see Gotchas) |
| `quit` | close the browser and exit |

Stop both servers (Windows has no `lsof`; find the PID via `netstat` and use
`taskkill`):

```bash
netstat -ano | grep -E ':(8000|5173)' | grep LISTENING
# then, per PID printed above:
taskkill //PID <pid> //F
```

## Run (human path)

```bash
uv run uvicorn api.main:app --reload --app-dir packages/api/src   # http://localhost:8000
cd client && npm run dev                                          # http://localhost:5173
```
Ctrl-C each to stop. Opening `http://localhost:5173` in a real browser hits
the same broken button described in Gotchas.

## Test

```bash
uv run pytest
```
2 passed (`test_graph.py`, `test_health.py`) — the whole suite today, no
flakes observed.

---

## Gotchas

- **The client's "Just me" / "Start a group" buttons are broken today.**
  `client/src/api/sessions.ts` calls `fetch("/api/sessions", ...)`; Vite's
  proxy (`client/vite.config.ts`) forwards `/api/*` to `http://localhost:8000`
  **without stripping the `/api` prefix**, but the FastAPI router is mounted
  at `/sessions`, not `/api/sessions`. So the proxied request 404s, `createSession`
  throws, and the button click silently does nothing (unhandled rejection,
  no UI feedback) — confirmed via `console --errors`:
  `Error: Failed to create session: 404`. `POST http://localhost:8000/sessions`
  directly works fine (see the Run section) — use that to get a session id
  and navigate to `/session/<id>` directly to exercise the rest of the client.
  Note the error only shows up in the console if you `sleep` briefly after
  the click before checking — `click` resolves as soon as the DOM event
  fires, not once the `fetch` it kicked off settles, so a `console --errors`
  run immediately after sees nothing yet.
- **`driver.mjs` selectors are split on the first space** (`fill <selector> <value>`),
  so a selector containing spaces (e.g. an attribute-value selector like
  `input[placeholder="What are you in the mood for?"]`) breaks the split.
  Use a simpler selector (`input`, `button:has-text("Just me")` — the
  `:has-text()` pseudo-class is fine since it's one token to `split(" ")`'s
  purposes as written) or extend the parser if you need real multi-word CSS.
- **Playwright's browser cache can be for the wrong version.** This
  environment had a Chromium build cached under `ms-playwright` already, but
  it didn't match the `playwright` npm version that got installed
  (`Executable doesn't exist at ...chromium_headless_shell-1243...`). Fix:
  `npx --prefix .claude/skills/run-hangry playwright install chromium`
  (downloads ~300MB, one-time).
- **`.env.example` doesn't exist**, despite the README's first setup step
  being `cp .env.example .env`. Not needed for anything in this skill (see
  Setup), but if you do need real credentials for `ANTHROPIC_API_KEY` /
  `GOOGLE_PLACES_API_KEY` / `DATABASE_URL`, you're writing `.env` from
  scratch using `packages/api/src/api/core/config.py`'s field names.

## Troubleshooting

- **`page.goto: net::ERR_ABORTED` on the very first `nav`**: the dev server
  wasn't actually ready yet (a fixed `sleep` beat the poll). Poll
  `curl -sf http://localhost:5173/` instead of sleeping a fixed amount.
- **Driver commands run out of order / "Target page, context or browser has
  been closed" on unrelated commands**: only happens if you rewrite the
  driver's stdin loop to fire `readline`'s `line` event handler without
  awaiting it — commands race and `quit` can close the browser mid-flight.
  The shipped driver uses `for await (const line of rl)` specifically to
  avoid this; keep that shape if you modify it.
- **`EADDRINUSE` on port 8000 or 5173 on a re-run**: a previous server is
  still up. `netstat -ano | grep -E ':(8000|5173)' | grep LISTENING`, then
  `taskkill //PID <pid> //F` (there's no `lsof`/`pkill` on this Windows box).
