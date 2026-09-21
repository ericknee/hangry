# Migrations

Run `alembic init .` from `packages/api/` to scaffold `env.py` and
`versions/` here once the `sessions` table (or any schema change) is ready
to be migrated, rather than relying on `Base.metadata.create_all` past
Phase 1.
