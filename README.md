# Hangry

Solo restaurant picker: choose a location, answer a few taps, and swipe through a ranked shortlist
from one Google Places search. No LLM. See `docs/filtering-plan.md` for the MVP spec and decisions.

## Layout

- `packages/agent` — search pipeline: query building, Places retrieval, ranking
- `packages/api` — FastAPI service (sessions, search/results endpoints, Postgres)
- `client` — React + Tailwind + Vite frontend

`packages/agent` and `packages/api` are a single [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/):
one lockfile, shared tooling, `api` depends on `agent` as a local editable package.

## First-time setup

```bash
cp .env.example .env        # fill in GOOGLE_PLACES_API_KEY and the POSTGRES_* values
docker compose up -d        # starts Postgres (credentials come from .env)
uv sync --all-packages      # installs both packages + dev deps into one venv
uv run python -m alembic -c packages/api/alembic.ini upgrade head   # creates the sessions table

cd client && npm install    # frontend dependencies
```

## Run

```bash
npm run dev                 # from the repo root: API and frontend together
```

Or separately, from the repo root: `npm run be` (API) and `npm run fe` (frontend on http://localhost:5173).

## Common commands

```bash
uv run python -m pytest    # run all tests across both packages
uv run ruff check .        # lint
uv run ruff format .       # format
```
