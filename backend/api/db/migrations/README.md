# Migrations

Alembic, async template. Config is `backend/alembic.ini`; the database URL comes from
`DATABASE_URL` in the repo-root `.env` (see `env.py`), not from the ini file. The API's settings
find `.env` by absolute path, so these work from any folder.

From the repo root:

```bash
uv run python -m alembic -c backend/alembic.ini upgrade head                           # apply
uv run python -m alembic -c backend/alembic.ini revision --autogenerate -m "message"   # after editing db/models.py
```


`--autogenerate` needs Postgres running (`docker compose up -d`). Review the generated file before
applying it.
