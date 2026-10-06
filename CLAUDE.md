# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Hangry — a solo restaurant picker (MVP). The user chooses a location and answers a few taps, the
backend runs **one** Google Places search, and the user swipes through a ranked shortlist. There is
**no LLM** anywhere in the flow. Group sessions, the cuisine veto step and photos are not built (see
"Not built yet"). Product and technical decisions live in `docs/filtering-plan.md`.

The earlier LangGraph graph, aggregation strategies (`maximin`, `borda`, `average_utility`) and
Claude client were removed as unused; they remain in git history.

## Layout

- `packages/agent` — the search pipeline: query building, Places retrieval, ranking (`agent.*`)
- `packages/api` — FastAPI service: sessions, search/results endpoints, Postgres (`api.*`)
- `client` — React + Tailwind + Vite frontend
- `docs/filtering-plan.md` — MVP spec, decisions, costs, future work

`packages/agent` and `packages/api` are a single [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/):
one lockfile, shared tooling; `api` depends on `agent` as a local editable package (`tool.uv.sources`
in `packages/api/pyproject.toml`).

## Commands

First-time setup:

```bash
cp .env.example .env        # fill in GOOGLE_PLACES_API_KEY and the POSTGRES_* values; DATABASE_URL must match them
docker compose up -d        # starts Postgres (credentials come from .env)
uv sync --all-packages      # installs both packages + dev deps into one venv
uv run python -m alembic -c packages/api/alembic.ini upgrade head   # creates the sessions table

cd client && npm install && npm run dev   # frontend on http://localhost:5173
```

Run the API (separate terminal, repo root):

```bash
uv run uvicorn api.main:app --reload --app-dir packages/api/src
```

Backend:

```bash
uv run python -m pytest                # all tests across both packages (`uv run pytest` fails on this Windows setup)
uv run python -m pytest packages/agent/tests/test_ranking.py   # single file
uv run ruff check .                    # lint
uv run ruff format .                   # format
```

Frontend (run from `client/`):

```bash
npm run dev       # Vite dev server
npm run build     # tsc -b && vite build
npm run lint      # eslint
```

## Search pipeline (`packages/agent`)

- `search_params.py` turns setup answers into search parameters. The search takes **one** place
  type and dietary wins it; the query is the craving if typed, else the default text for the winning
  type; walk/drive minutes become a radius (80 / 500 m per minute ÷ 1.3 detour, square bounding box).
- `retrieval.py` runs the search (open now, rating floor 3.5, one retry at 3.0 if under 5 results),
  drops non-operational places and maps results to `Candidate`s.
- `ranking.py` orders candidates by a Bayesian average of rating (prior weight 50 reviews, pool-average
  prior); unrated last; distance breaks ties.
- `questions.py` picks the next veto question by how evenly an attribute splits the remaining
  candidates. **Not wired in yet** (the veto step is deferred); it has tests.
- `state.py` holds the shared shapes (`Candidate`, `Question`).
- `clients/places.py` — Google Places API (New) client. Text Search is billed at the highest tier of
  any requested field: `SEARCH_FIELD_MASK` is **Enterprise** (rating, price level) and runs once per
  session; no Atmosphere fields, no photos. Adding fields can raise the tier and the bill — check
  `docs/filtering-plan.md` before changing the mask.

## API / persistence (`packages/api`)

- `POST /sessions` inserts a `SessionRecord` (initial query + location, coordinates rounded to 3
  decimals, ~110 m). It does not search.
- `POST /sessions/{id}/search` takes the setup answers, runs the one Places search, keeps the
  candidates in a 30-minute in-memory cache (`core/candidate_cache.py`; Google's terms limit stored
  Places content, so they are never written to the DB) and records the setup answers on the row.
  Places errors return 502.
- `GET /sessions/{id}/results` returns the cached candidates ranked, trimmed to user-facing fields;
  404 once the cache entry has expired (including after any server restart).
- DB is Postgres via async SQLAlchemy (`api/db/database.py`, `api/db/models.py`). Schema changes go
  through Alembic (`packages/api/alembic.ini`, migrations in `api/db/migrations/`); see
  `api/db/migrations/README.md`.
- Settings (`api/core/config.py`) load the repo-root `.env` by absolute path via `pydantic-settings`;
  `google_places_api_key` and `database_url` are required. Tests set dummy values in
  `packages/api/tests/conftest.py`.

## Frontend (`client`)

React Router pages under `client/src/pages/`: `LocationPage` (`/`, location search with a "Current
location" dropdown entry; choice held in `sessionStorage` via `lib/pendingLocation.ts`) →
`SearchPage` (`/search`, optional craving text; Next creates the session) → four setup pages under
`pages/setup/` (`/session/:sessionId/setup/{after,price,dietary,travel}`, one question each, answers
held in `sessionStorage` via `lib/setupAnswers.ts`; the last one runs the search behind a loading
screen) → `ShortlistPage` (`/session/:sessionId/shortlist`: swipeable `CardDeck` of
`RestaurantCard`s, top 3 first, "More recommendations" appends the rest).
`client/src/api/sessions.ts` calls the backend at `/api/sessions` (expects a dev proxy or same-origin
deploy — there's no absolute API base URL configured).

## Not built yet

- Group sessions: invites, the join page (the API returns a `share_url` for `mode: "group"` that
  nothing serves), host-location search.
- The cuisine veto question (selection logic exists in `questions.py`, no endpoint or page).
- Place photos, session resume after a refresh (answers live in `sessionStorage`), a persisted final pick.
