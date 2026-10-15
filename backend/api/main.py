import asyncio
import contextlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agent.places_client import PlacesClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.db.database import async_session
from api.places.router import router as places_router
from api.sessions.cache import CandidateCache
from api.sessions.retention import run_purge_loop
from api.sessions.router import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Loads .env once; a missing key fails here at startup rather than per request.
    settings = get_settings()
    app.state.places = PlacesClient(api_key=settings.google_places_api_key)
    app.state.candidates = CandidateCache()
    purge = asyncio.create_task(run_purge_loop(async_session, days=settings.session_retention_days))
    yield
    purge.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await purge
    await app.state.places.aclose()


app = FastAPI(title="Hangry API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(places_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
