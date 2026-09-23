# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Hangry — a group & solo restaurant decision agent. A LangGraph-orchestrated
graph does adaptive preference elicitation per member, then aggregates member preferences into a
fair consensus shortlist. Very early Phase 1: most node logic is still stubbed (see "Current state"
below) — don't assume TODOs are dead code, they mark exactly what's unimplemented.

## Layout

- `packages/agent` — the LangGraph graph, aggregation strategies, LLM/Places clients (`agent.*`)
- `packages/api` — FastAPI service: session routing, auth, WebSocket live updates (`api.*`)
- `client` — React + Tailwind + Vite frontend
- `scripts/smoke_test.py` — end-to-end credentials + graph-skeleton check

`packages/agent` and `packages/api` are a single [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/):
one lockfile, shared tooling; `api` depends on `agent` as a local editable package (`tool.uv.sources`
in `packages/api/pyproject.toml`).

## Commands

First-time setup:

```bash
cp .env.example .env        # fill in GOOGLE_PLACES_API_KEY (the others are optional for now)
docker compose up -d        # starts Postgres on localhost:5432
uv sync --all-packages      # installs both packages + dev deps into one venv
uv run python scripts/smoke_test.py   # verifies graph + both API keys work

cd client && npm install && npm run dev   # frontend on http://localhost:5173
```

Run the API (separate terminal, repo root):

```bash
uv run uvicorn api.main:app --reload --app-dir packages/api/src
```

Backend:

```bash
uv run pytest                          # run all tests across both packages
uv run pytest packages/agent/tests/test_graph.py::test_graph_compiles  # single test
uv run ruff check .                    # lint
uv run ruff format .                   # format
```

Frontend (run from `client/`):

```bash
npm run dev       # Vite dev server
npm run build     # tsc -b && vite build
npm run lint      # eslint
```

## Architecture: the LangGraph graph

`packages/agent/src/agent/graph.py` builds the core state machine:

```
Start -> elicit (parallel Send per member) -> aggregate & retrieve
      -> consensus reached? --no--> back to elicit (targeted follow-up)
                            --yes-> present shortlist -> log selection -> End
```

- **Solo mode is not a separate graph.** It's this exact graph invoked with `members` of length 1 —
  the aggregation node becomes a pass-through and consensus resolves on the first pass. Never branch
  solo vs. group in graph structure; if you need different behavior, it belongs in the member-count
  check, not a new path.
- **Fan-out**: `elicit` runs once per member in parallel via LangGraph's `Send` API
  (`agent/nodes/elicit.py`) — branches must stay independent, no cross-member blocking.
- **Consensus loop**: `_consensus_reached` in `graph.py` routes back to `elicit` for a targeted
  follow-up on whichever member is blocking consensus, or forward to `present`. `round_count` vs.
  `max_rounds` bounds the loop so a non-converging group still terminates with a best-effort
  shortlist (`packages/api/src/api/core/config.py` sets defaults: `consensus_threshold=0.7`,
  `max_rounds=4`).
- **State shape**: `packages/agent/src/agent/state.py` (`HangryState`, `MemberState`,
  `Candidate`) is the single source of truth for what flows through every node — read it before
  touching any node.

## Aggregation strategies

`packages/agent/src/agent/aggregation/` holds multiple candidate-scoring strategies
(`average_utility`, `maximin`, `borda`) behind the `STRATEGIES` map in `aggregation/__init__.py`.
Which one ships as default is an open evaluation question (currently `maximin`, wired directly in
`nodes/aggregate.py` as `DEFAULT_STRATEGY`), not a settled decision — don't treat the current
default as final without checking whether the evaluation plan has since picked a winner. Borda is
scored across the whole candidate set at once (not per-candidate like the others), so it isn't in
the `STRATEGIES` map and must be invoked separately.

## LLM / external API clients

- `agent/clients/claude.py` — thin `AsyncAnthropic` wrapper for exactly two jobs: generating one
  adaptive elicitation question + tap options, and writing the shortlist explanation. By design,
  elicitation answers are tap-selected from generated options, not free-typed — there's no
  free-text NLU surface to build here; don't add one.
- `agent/clients/places.py` — Google Places API (New) client. Deliberately uses two field masks:
  `SEARCH_FIELD_MASK` (Essentials tier, cheap) for bulk candidate search, `DETAIL_FIELD_MASK`
  (Pro/Enterprise tier) only for the handful of shortlist finalists. Keep new Places calls on the
  cheaper mask unless they genuinely need Pro-tier fields (rating, reviews, photos).

## API / persistence

- `packages/api/src/api/routers/sessions.py` builds the graph once at import time (`_graph =
  build_graph()`) and reuses it per request.
- DB is Postgres via async SQLAlchemy (`api/db/database.py`, `api/db/models.py`). Phase 1 scope is
  session logs only (`SessionRecord`: id, mode, created_at, last-known state snapshot as JSON, final
  pick). No Alembic migrations exist yet — schema currently relies on `Base.metadata.create_all`;
  see `api/db/migrations/README.md` for when/how to scaffold Alembic (`alembic init .` from
  `packages/api/`) once the schema is ready to be migrated for real.
- `api/ws/manager.py` (`SessionConnectionManager`) broadcasts live per-session updates (e.g. "2 of 3
  members done") over WebSocket as parallel elicit branches complete.
- Settings (`api/core/config.py`) load from `.env` via `pydantic-settings`; Only
  `google_places_api_key` is required; `database_url` and `anthropic_api_key` are temporarily
  optional (nothing in the API uses the DB or Claude yet) — make them required again once wired.

## Frontend

React Router pages under `client/src/pages/`: `HomePage` (create session) → `ElicitationPage`
(`/session/:sessionId`, tap-option question flow) → `ShortlistPage` (`/session/:sessionId/shortlist`).
`client/src/api/sessions.ts` calls the backend at `/api/sessions` (expects a dev proxy or same-origin
deploy — there's no absolute API base URL configured). Elicitation UI is tap-to-select
(`TapOptionQuestion` component), matching the "no free-text NLU" decision on the backend.

## Current state (don't be surprised by stubs)

- `elicit_member` always asks exactly one question then marks the member done — no real
  expected-information-gain stopping rule yet.
- `aggregate_and_retrieve` scores whatever candidates are already in state — no real Places
  retrieval/re-ranking wired in yet.
- `sessions.py`'s `create_session` doesn't persist a `SessionRecord` or invoke the graph yet.
- `ElicitationPage` renders a hardcoded placeholder question instead of fetching one.
