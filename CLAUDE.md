# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Hangry — a solo restaurant picker (MVP). The user chooses a location and answers a few taps, the
backend runs **one** Google Places search, and the user swipes through a ranked shortlist. There is
**no LLM** anywhere in the flow. Group sessions and the cuisine veto step are not built (see
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

Container (one image: API + built frontend; the same image runs the purge job with
`python -m api.sessions.retention`). Pass secrets at run time, never bake `.env` in:

```bash
docker build -t hangry .
docker run --rm -p 8080:8080 -e DATABASE_URL=... -e GOOGLE_PLACES_API_KEY=... hangry   # http://localhost:8080
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
  type: dietary wins it for breakfast/lunch/dinner, but for coffee & dessert and drinks the meal
  keeps the type and dietary is added to the query text ("vegan drinks"); the query is the craving if typed, else the default text for the winning
  type; walk/drive minutes become a radius (80 / 500 m per minute ÷ 1.3 detour, square bounding box).
- `search/retrieval.py` runs the search (open now, rating floor 3.5, one retry at 3.0 if under 5 results),
  drops non-operational places and maps results to `Candidate`s.
- `search/ranking.py` orders candidates by a Bayesian average of rating (prior weight 50 reviews, pool-average
  prior); unrated last; distance breaks ties.
- `veto/questions.py` picks the next veto question by how evenly an attribute splits the remaining
  candidates. **Not wired in yet** (the veto step is deferred); it has tests.
- `types.py` holds the pipeline's shared types: `Candidate`, `SearchParams`, `Question`, `QuestionOption`.
- `places_client.py` — Google Places API (New) client. Text Search is billed at the highest tier of
  any requested field: `SEARCH_FIELD_MASK` is **Enterprise** (rating, price level; `places.photos` is Pro) and runs once per
  session; no Atmosphere fields. `open_photo` fetches one image (a separate billed request). Adding fields can raise the tier and the bill — see
  "Places cost" under "Decisions" before changing the mask.

## API / persistence (`backend/api`)

Every route is mounted under `API_PREFIX` (`/api`, in `api/main.py`). When `STATIC_DIR` is set (the Docker image
sets it) `api/frontend.py` also serves the built React app from the same origin: real files as-is, any other path
falls back to `index.html`, unknown `/api/*` paths stay JSON 404s. There is no CORS: dev uses Vite's `/api` proxy,
prod is same-origin.

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
- `GET /sessions/{id}/restaurants/{place_id}/photo` streams one 800px photo via `PlacesClient.open_photo`
  (`skipHttpRedirect`, then the CDN `photoUri` without the API key) using `api/media.py`'s
  `stream_upstream`. Photo names expire, so only the cached candidate holds them; the browser may cache
  the image for the 30-minute TTL. 404 if no photo, 502 on Places errors. `RestaurantOut.photo` carries
  the author credit Google requires; the card shows it and falls back to the cuisine gradient.
- Rate limits (`api/ratelimit.py`): in-memory sliding windows keyed by client IP (per minute) and, for photo and search,
  by session id (per 30 minutes). Applied as route dependencies; values are `RATE_LIMIT_*` settings (0 = off), over the
  limit the API returns 429 with `Retry-After`. Counters reset on restart and are exact only because there is one instance.
  Tests set them to 0 in `backend/tests/api/conftest.py`.
- DB is Postgres via async SQLAlchemy (`api/db/database.py`, `api/db/models.py`). Schema changes go
  through Alembic (`backend/alembic.ini`, migrations in `api/db/migrations/`); see
  `api/db/migrations/README.md`.
- Settings (`api/config.py`) load the repo-root `.env` by absolute path via `pydantic-settings`;
  `google_places_api_key` and `database_url` are required. `ENVIRONMENT=prod` turns off `/docs`, `/redoc` and `/openapi.json` (default `dev`); the app is built by `create_app(settings)` in `api/main.py`. Tests set dummy values in
  `backend/tests/api/conftest.py`.

## Frontend (`client`)

Organized by feature under `client/src/features/`:
- `location/` — `LocationPage` (`/`, location search with a "Current location" dropdown entry; the
  choice is held in `sessionStorage` via `pendingLocation.ts`).
- `setup/` — `SearchPage` (`/search`, optional craving text; Next creates the session) and the four
  one-question pages (`/session/:sessionId/setup/{after,price,dietary,travel}`). Answers are held in
  `sessionStorage` via `setupAnswers.ts`; the last page runs the search behind a loading screen.
- `legal/` — `TermsPage` (`/terms`) and `PrivacyPage` (`/privacy`), plain static pages. `LegalLinks` (Terms · Privacy)
  is rendered by `Page` on every screen. **Update the policy whenever data flows change** (what is stored, who
  receives it, retention).
- `shortlist/` — `ShortlistPage` (`/session/:sessionId/shortlist`): a swipeable `CardDeck` of
  `RestaurantCard`s, top 3 first, "More recommendations" appends the rest.

`components/` holds only shared UI (`OptionChips`, `LoadingScreen`, `Toast`). Errors are shown as a
top-of-screen toast: call `useToast().showError(userMessage(error, "friendly fallback"))` (`userMessage`
is in `api/http.ts`; backend `detail` stays in the console, not the UI). `routes.ts` lists every URL
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
  only (dietary wins for breakfast/lunch/dinner; for coffee & dessert and drinks the meal type
  stays and dietary goes in the query text); query = the craving if typed, else the default text for the winning type.
- **Ranking:** Bayesian average, prior weight 50 reviews, pool-average prior.
- **Database role (RLS):** `sessions` has row level security on with no policies (migration 0002), so Supabase's
  REST API can read nothing. The app must connect as the table owner or a `BYPASSRLS` role (Supabase's `postgres.<ref>`
  pooler user qualifies); a restricted role would see zero rows. Timestamps are timezone-aware UTC (`created_at` is `timestamptz`).
- **Storage:** places results (including photo names) are only in the 30-minute in-memory cache; the DB stores IDs, setup
  answers, the typed craving (`initial_query`, max 100 chars, the only free text) and rounded (3-decimal)
  coordinates. Sessions older than `session_retention_days` (30) are
  deleted by `api/sessions/retention.py`, run as a daily job (`python -m api.sessions.retention`; Cloud Run Job
  + Cloud Scheduler), not inside the API process. One photo per restaurant, fetched on demand through the proxy.
- **Places cost:** Text Search is billed at the highest tier of any requested field. Enterprise
  (rating, price) is about $35 per 1,000 searches with 1,000 free a month; Pro is about $32 per 1,000
  with 5,000 free but has no rating or price; Atmosphere is about $40 per 1,000. Figures come from
  Google's pricing page as read in 2026-10 and have not been checked against a live call or the bill.
  A place photo is a separate request at about $0.007 each.
- **City autocomplete cost:** the client makes one session token (UUID) per typing session and sends it with
  every autocomplete call and the city lookup (`session_token` query param); it is replaced after each
  selection. Only the first 12 requests in a session bill as Autocomplete Requests (about $2.83 per 1,000,
  10,000 free a month), so the token saves little on short city searches. The lookup ends the session with
  `LOCATION_FIELD_MASK`, which includes `displayName` (Pro). Google bills a session that ends in a Pro-or-higher
  Place Details request at the Enterprise + Atmosphere rate; an Essentials-only mask (`id,formattedAddress,location`)
  would be Place Details Essentials (about $5 per 1,000, 10,000 free). Check the SKU breakdown on the first bill.

- **US only:** the service is for US users. City autocomplete is limited with `includedRegionCodes: ["us"]`; blocking
  other countries has to happen at the edge (e.g. Cloudflare), not in this app.
- **Deploy constraint (Cloud Run):** candidates live in the process's memory, and Google's terms stop us storing them
  elsewhere, so run exactly one always-on instance (`--min-instances=1 --max-instances=1`). Scaling to zero or out
  loses results (404 on `/results`), (the purge is a separate job, so it does not depend on this).

## Not built yet

- Group sessions: invites, the join page (the API returns a `share_url` for `mode: "group"` that
  nothing serves), host-location search.
- The cuisine veto question (selection logic exists in `veto/questions.py`, no endpoint or page).
- Session resume after a refresh (answers live in `sessionStorage`), a persisted final pick.
