import os

# Settings require these at import time; tests never connect to either service.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("GOOGLE_PLACES_API_KEY", "test-key")
