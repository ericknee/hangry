# Hangry

Solo restaurant picker: choose a location, answer a few taps, and swipe through a ranked shortlist
from one Google Places search. No LLM. See `CLAUDE.md` for the architecture and decisions.

## Layout

- `backend/agent` — search pipeline: query building, Places retrieval, ranking
- `backend/api` — FastAPI service (sessions, search/results endpoints, Postgres)
- `backend/tests` — backend tests
- `client` — React + Tailwind + Vite frontend

The backend is one Python project (root `pyproject.toml`, one lockfile). `agent` is the pure search
logic; `api` imports from it, never the reverse.

## First-time setup

```bash
cp .env.example .env        # fill in GOOGLE_PLACES_API_KEY and the POSTGRES_* values
docker compose up -d        # starts Postgres (credentials come from .env)
uv sync                     # installs the backend + dev deps into one venv
uv run python -m alembic -c backend/alembic.ini upgrade head   # creates the sessions table

cd client && npm install    # frontend dependencies
```

## Run

```bash
npm run dev                 # from the repo root: API and frontend together
```

Or separately, from the repo root: `npm run be` (API) and `npm run fe` (frontend on http://localhost:5173).

## Common commands

```bash
uv run python -m pytest    # run all backend tests
uv run ruff check .        # lint
uv run ruff format .       # format
```
