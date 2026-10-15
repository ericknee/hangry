import os

# Settings require these at import time; tests never connect to either service.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("GOOGLE_PLACES_API_KEY", "test-key")

# The shared app is hit many times from one test client; rate limiting is tested on its own apps.
for _name in (
    "PHOTO_IP_PER_MIN",
    "PHOTO_SESSION",
    "SEARCH_IP_PER_MIN",
    "SEARCH_SESSION",
    "SESSION_CREATE_IP_PER_MIN",
    "PLACES_IP_PER_MIN",
):
    os.environ.setdefault(f"RATE_LIMIT_{_name}", "0")
