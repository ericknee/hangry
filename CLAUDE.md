# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Hangry — a solo restaurant picker (MVP). The user chooses a location and answers a few taps, the
backend runs **one** Google Places search, and the user swipes through a ranked shortlist. There is
**no LLM** anywhere in the flow. Group sessions, the cuisine veto step and photos are not built (see
"Not built yet"). Key product and technical decisions are listed under "Decisions" below.

The earlier LangGraph graph, aggregation strategies (`maximin`, `borda`, `average_utility`) and
Claude client were removed as unused; they remain in git history.

## Layout

- `backend/agent` — the search pipeline: query building, Places retrieval, ranking (`agent.*`)
- `backend/api` — FastAPI service: sessions, search/results endpoints, Postgres (`api.*`)
- `backend/tests` — backend tests, in `agent/` and `api/` folders mirroring the code
- `client` — React + Tailwind + Vite frontend

The backend is one Python project (root `pyproject.toml`, one lockfile). Keep `agent` free of web and
database code: `api` imports from `agent`, never the reverse.

## Commands

First-time setup:

```bash
cp .env.example .env        # fill in GOOGLE_PLACES_API_KEY and the POSTGRES_* values; DATABASE_URL must match them
docker compose up -d        # starts Postgres (credentials come from .env)
uv sync                     # installs the backend + dev deps into one venv
uv run python -m alembic -c backend/alembic.ini upgrade head   # creates the sessions table

cd client && npm install && npm run dev   # frontend on http://localhost:5173
```

Run the API (separate terminal, repo root):

```bash
uv run uvicorn api.main:app --reload --app-dir backend
```

Backend:

```bash
uv run python -m pytest                # all backend tests (`uv run pytest` fails on this Windows setup)
uv run python -m pytest backend/tests/agent/test_ranking.py   # single file
uv run ruff check .                    # lint
uv run ruff format .                   # format
```

Frontend (run from `client/`):

```bash
npm run dev       # Vite dev server
npm run build     # tsc -b && vite build
npm run lint      # eslint
npm run gen:api   # regenerate the API types after changing backend/api/**/types.py
```

## Search pipeline (`backend/agent`)

- `search/params.py` turns setup answers into search parameters. The search takes **one** place
  type and dietary wins it; the query is the craving if typed, else the default text for the winning
  type; walk/drive minutes become a radius (80 / 500 m per minute ÷ 1.3 detour, square bounding box).
- `search/retrieval.py` runs the search (open now, rating floor 3.5, one retry at 3.0 if under 5 results),
  drops non-operational places and maps results to `Candidate`s.
- `search/ranking.py` orders candidates by a Bayesian average of rating (prior weight 50 reviews, pool-average
  prior); unrated last; distance breaks ties.
- `veto/questions.py` picks the next veto question by how evenly an attribute splits the remaining
  candidates. **Not wired in yet** (the veto step is deferred); it has tests.
- `types.py` holds the pipeline's shared types: `Candidate`, `SearchParams`, `Question`, `QuestionOption`.
- `places_client.py` — Google Places API (New) client. Text Search is billed at the highest tier of
  any requested field: `SEARCH_FIELD_MASK` is **Enterprise** (rating, price level) and runs once per
  session; no Atmosphere fields, no photos. Adding fields can raise the tier and the bill — see
  "Places cost" under "Decisions" before changing the mask.

## API / persistence (`backend/api`)

Organized by feature: `sessions/` (`router.py` is HTTP only, `service.py` holds the logic and raises
domain errors the router maps to status codes, plus `types.py` and `cache.py`) and `places/`
(city autocomplete and lookup). `config.py` holds settings, `deps.py` the shared dependency getters,
`db/` the models, connection and migrations. Each feature's request/response types are Pydantic
models in its `types.py`.

- `POST /sessions` inserts a `SessionRecord` (initial query + location, coordinates rounded to 3
  decimals, ~110 m). It does not search.
- `POST /sessions/{id}/search` takes the setup answers, runs the one Places search, keeps the
  candidates in a 30-minute in-memory cache (`sessions/cache.py`; Google's terms limit stored
  Places content, so they are never written to the DB) and records the setup answers on the row.
  Places errors return 502.
- `GET /sessions/{id}/results` returns the cached candidates ranked, trimmed to user-facing fields;
  404 once the cache entry has expired (including after any server restart).
- DB is Postgres via async SQLAlchemy (`api/db/database.py`, `api/db/models.py`). Schema changes go
  through Alembic (`backend/alembic.ini`, migrations in `api/db/migrations/`); see
  `api/db/migrations/README.md`.
- Settings (`api/config.py`) load the repo-root `.env` by absolute path via `pydantic-settings`;
  `google_places_api_key` and `database_url` are required. Tests set dummy values in
  `backend/tests/api/conftest.py`.

## Frontend (`client`)

Organized by feature under `client/src/features/`:
- `location/` — `LocationPage` (`/`, location search with a "Current location" dropdown entry; the
  choice is held in `sessionStorage` via `pendingLocation.ts`).
- `setup/` — `SearchPage` (`/search`, optional craving text; Next creates the session) and the four
  one-question pages (`/session/:sessionId/setup/{after,price,dietary,travel}`). Answers are held in
  `sessionStorage` via `setupAnswers.ts`; the last page runs the search behind a loading screen.
- `shortlist/` — `ShortlistPage` (`/session/:sessionId/shortlist`): a swipeable `CardDeck` of
  `RestaurantCard`s, top 3 first, "More recommendations" appends the rest.

`components/` holds only shared UI (`OptionChips`, `LoadingScreen`). `routes.ts` lists every URL
pattern; build concrete paths with react-router's `generatePath`. `api/` is the client's data layer:
`http.ts` is the shared request helper, `sessions.ts` and `places.ts` wrap the endpoints
(`/api/...`; expects a dev proxy or same-origin deploy — there's no absolute API base URL configured).

## Types

- **Naming:** "schema" is reserved for the database. Type definitions live in `types.py` (backend)
  and `types.ts` (client); table definitions are in `backend/api/db/models.py` with Alembic migrations.
- **Backend:** `backend/api/sessions/types.py` and `backend/api/places/types.py` hold the API's
  request/response models (Pydantic); `backend/agent/types.py` holds the pipeline's types.
- **Client:** `client/src/types.ts` is the one place to import types from. The API types in it are
  **generated** from the backend, so don't hand-write them; it also holds the client-only types
  (`SetupAnswers`, `PendingLocation`).
- **Workflow after changing a backend API type:** run `npm run gen:api` in `client/`. It dumps the
  FastAPI schema to `client/src/api/openapi.json` and generates `client/src/api/types.gen.ts` with
  `openapi-typescript`. Commit both. `backend/tests/api/test_openapi_snapshot.py` fails when the
  snapshot is stale.
- Output models should not give fields Python defaults (`= None`), because that makes the generated
  TypeScript fields optional; request models can.

## Decisions

- **Setup answers:** meal (breakfast / lunch / dinner / coffee & dessert / drinks, single-select),
  price (1–4 tiers, multi-select, none = any), dietary (none / vegetarian / vegan / halal,
  single-select), travel (walk or drive, 5–60 min slider, default 20).
- **Search filters:** open now; rating ≥ 3.5, retried once at 3.0 if under 5 results. One place type
  only (dietary wins); query = the craving if typed, else the default text for the winning type.
- **Ranking:** Bayesian average, prior weight 50 reviews, pool-average prior.
- **Storage:** places results are only in the 30-minute in-memory cache; the DB stores IDs, setup
  answers and rounded (3-decimal) coordinates. Photos are not fetched.
- **Places cost:** Text Search is billed at the highest tier of any requested field. Enterprise
  (rating, price) is about $35 per 1,000 searches with 1,000 free a month; Pro is about $32 per 1,000
  with 5,000 free but has no rating or price; Atmosphere is about $40 per 1,000. Figures come from
  Google's pricing page as read in 2026-10 and have not been checked against a live call or the bill.
  A place photo is a separate request at about $0.007 each.

## Not built yet

- Group sessions: invites, the join page (the API returns a `share_url` for `mode: "group"` that
  nothing serves), host-location search.
- The cuisine veto question (selection logic exists in `veto/questions.py`, no endpoint or page).
- Place photos, session resume after a refresh (answers live in `sessionStorage`), a persisted final pick.
