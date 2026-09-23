# Hangry

Group & solo restaurant decision agent — LangGraph-orchestrated adaptive
preference elicitation and fair-consensus aggregation.

## Layout

- `packages/agent` — the LangGraph graph, aggregation strategies, LLM/Places clients
- `packages/api` — FastAPI service (session routing, auth, WebSocket live updates)
- `client` — React + Tailwind + Vite frontend
- `scripts/smoke_test.py` — end-to-end credentials + skeleton check

`packages/agent` and `packages/api` are a single [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/):
one lockfile, shared tooling, `api` depends on `agent` as a local editable package.

## First-time setup

```bash
cp .env.example .env        # fill in GOOGLE_PLACES_API_KEY (the others are optional for now)
docker compose up -d        # starts Postgres on localhost:5432
uv sync --all-packages      # installs both packages + dev deps into one venv
uv run python scripts/smoke_test.py   # verifies graph + both API keys work

cd client && npm install && npm run dev   # frontend on http://localhost:5173
```

In another terminal:

```bash
uv run uvicorn api.main:app --reload --app-dir packages/api/src
```

## Common commands

```bash
uv run pytest              # run all tests across both packages
uv run ruff check .        # lint
uv run ruff format .       # format
```
