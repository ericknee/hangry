from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agent.clients.places import PlacesClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import get_settings
from api.routers import places, sessions


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Loads .env once; a missing key fails here at startup rather than per request.
    settings = get_settings()
    app.state.places = PlacesClient(api_key=settings.google_places_api_key)
    yield
    await app.state.places.aclose()


app = FastAPI(title="Hangry API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(places.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
