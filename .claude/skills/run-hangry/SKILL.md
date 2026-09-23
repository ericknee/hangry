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

A `.env` with a real `GOOGLE_PLACES_API_KEY` is required: the API's startup
hook (`api/main.py` `lifespan`) loads settings once and builds the shared
Places client, so without the key uvicorn exits with "Application startup
failed" and the `/health` poll below times out.

```bash
cp .env.example .env    # then fill in GOOGLE_PLACES_API_KEY
```

`DATABASE_URL` and `ANTHROPIC_API_KEY` are optional for now (nothing in the API
uses the DB or Claude yet), so Postgres doesn't need to be running. Settings
are read once per process, so restart the API after editing `.env`.

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

# 2. Client — port 5173, proxies /api/* to :8000 (stripping the /api prefix)
(cd client && npm run dev > /tmp/client.log 2>&1 &)
timeout 15 bash -c 'until curl -sf http://localhost:5173/ >/dev/null; do sleep 0.5; done'
```

If either port is already taken (the user often has their own dev servers
up), uvicorn logs `[Errno 10048]` and exits while Vite silently moves to 5174 —
the `curl` polls still succeed against the *user's* servers. Check the logs
before trusting which servers you're driving; see Gotchas.

Drive it — `driver.mjs` reads one command per line from stdin against a
single headless Chromium page. This is the real "create a solo session" flow
(it calls Google Places for autocomplete and the restaurant search):

```bash
node .claude/skills/run-hangry/driver.mjs <<'EOF'
nav http://localhost:5173
wait-for text=Hangry?
screenshot 01-home
fill input[placeholder^=Enter] Dublin
wait-for text=Dublin, Ireland
click button:has-text("Dublin, Ireland")
wait-for input[value="Dublin, Ireland"]
fill input[placeholder^=Sushi] pizza
screenshot 02-filled
click button:has-text("Next")
wait-for text=How far are you willing to travel
eval location.pathname
screenshot 03-elicitation
console --errors
quit
EOF
```

Screenshots land in `.claude/skills/run-hangry/screenshots/`. The
`wait-for input[value=...]` after picking a suggestion matters: the click
fires a city lookup (`/api/places/cities/<id>`) and only sets the field — and
the location sent with the session — once it resolves. Clicking Next before
then creates a session with no location (see Gotchas).

To jump straight to the elicitation/shortlist pages without the home flow,
get a session id from the API and navigate there:

```bash
SID=$(curl -s -X POST http://localhost:8000/sessions   -H "Content-Type: application/json"   -d '{"mode":"solo","initial_query":"tacos"}'   | node -e "process.stdin.on('data', d => console.log(JSON.parse(d).session_id))")

node .claude/skills/run-hangry/driver.mjs <<EOF
nav http://localhost:5173/session/$SID
wait-for text=How far are you willing to travel
screenshot 04-elicitation
click button:has-text("15 min")
nav http://localhost:5173/session/$SID/shortlist
wait-for text=Your shortlist
screenshot 05-shortlist
quit
EOF
```

To check the Places endpoints without a browser (note: no `/api` prefix when
hitting the API directly):

```bash
curl -s "http://localhost:8000/places/autocomplete?input=Dublin"
```

Driver commands:

| command | what it does |
|---|---|
| `nav <url>` | navigate the page |
| `wait-for text=<substring>` | wait up to 10s for text to appear |
| `wait-for <css-selector>` | wait up to 10s for a selector |
| `click <css-selector>` | click (the whole rest of the line is the selector, spaces OK) |
| `fill <css-selector> [value...]` | fill an input; no value clears it (selector must have no spaces — see Gotchas) |
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
Ctrl-C each to stop. Needs the same `.env` as above.

## Test

```bash
uv run python -m pytest
```
(Plain `uv run pytest` fails on this Windows box with "Failed to canonicalize
script path"; going through `python -m` avoids the broken shim.)
2 passed (`test_graph.py`, `test_health.py`) — the whole suite today, no
flakes observed.

---

## Gotchas

- **Next doesn't require a location, and failures are silent.** If Next is
  clicked before a suggestion is picked (or before the city lookup resolves),
  the session is created with no location and zero candidates — no warning.
  If `POST /api/sessions` fails, `createSession` throws an unhandled rejection
  and the button just does nothing. `click` resolves as soon as the DOM event
  fires, not once the `fetch` settles, so wait on a DOM signal (e.g.
  `wait-for text=How far are you willing to travel`) or `sleep` briefly
  before `console --errors`, or the error won't be there yet.
- **Places failures show up as an empty dropdown, not an error.** The client
  swallows autocomplete errors. If `wait-for text=<city>` times out, check the
  API log: a 502 means Google rejected the call (bad key, API not enabled,
  quota); a startup failure means `.env` is missing the key.
- **Your servers may not be the ones you're driving.** Port collisions (see
  Run) mean the driver can end up hitting the user's already-running servers.
  That's usually fine (same code, `--reload`), but check `api.log` /
  `client.log` for `10048` / "Port 5173 is in use" before blaming the code,
  and only `taskkill` PIDs you started.
- **`fill` splits selector from value on the first space**, so a `fill`
  selector can't contain spaces (e.g. `input[placeholder="Enter your location..."]`).
  Use a space-free prefix match like `input[placeholder^=Enter]`. `click` and
  `wait-for` take the whole rest of the line, so `button:has-text("Dublin, Ireland")`
  and `input[value="Dublin, Ireland"]` are fine there.
- **Playwright's browser cache can be for the wrong version.** This
  environment had a Chromium build cached under `ms-playwright` already, but
  it didn't match the `playwright` npm version that got installed
  (`Executable doesn't exist at ...chromium_headless_shell-1243...`). Fix:
  `npx --prefix .claude/skills/run-hangry playwright install chromium`
  (downloads ~300MB, one-time).

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
