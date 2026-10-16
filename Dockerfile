# One image for the whole app: the API serves the built React frontend from the same origin.
# The same image runs the daily purge job: override the command with `python -m api.sessions.retention`.

# --- Stage 1: build the frontend -------------------------------------------------------------
FROM node:22-slim AS client
WORKDIR /client
COPY client/package.json client/package-lock.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# --- Stage 2: Python dependencies ------------------------------------------------------------
FROM python:3.12-slim AS deps
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
# --no-install-project: the code runs straight from backend/, so only the dependencies are installed
# (and this layer stays cached until the lockfile changes).
RUN uv sync --frozen --no-dev --no-install-project

# --- Stage 3: runtime ------------------------------------------------------------------------
FROM python:3.12-slim
RUN useradd --system --create-home --uid 1000 app
WORKDIR /app
COPY --from=deps /app/.venv /app/.venv
COPY backend/ /app/backend/
COPY --from=client /client/dist /app/static
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1 \
    STATIC_DIR=/app/static \
    ENVIRONMENT=prod
USER app
EXPOSE 8080
# Exactly one worker: candidates live in this process's memory (see CLAUDE.md "Deploy constraint").
# Cloud Run sets PORT. --no-proxy-headers: uvicorn would trust the client-controlled left side of
# X-Forwarded-For; api/ratelimit.py reads the header itself (TRUSTED_PROXY_COUNT).
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --no-proxy-headers"]
