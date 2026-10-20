from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from agent.places_client import PlacesClient
from fastapi import APIRouter, FastAPI

from api.config import Settings, get_settings
from api.db.database import async_session
from api.frontend import mount_frontend
from api.ratelimit import RateLimiter
from api.routers.groups_router import router as groups_router
from api.routers.places_router import router as places_router
from api.routers.sessions_router import router as sessions_router
from api.utils.candidate_cache import CandidateCache
from api.utils.event_hub import EventHub
from api.utils.start_guard import StartGuard

# Every API route lives under this prefix; the rest of the URL space belongs to the frontend.
API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Loads .env once; a missing key fails here at startup rather than per request.
    settings = get_settings()
    app.state.places = PlacesClient(api_key=settings.google_places_api_key)
    app.state.candidates = CandidateCache()
    app.state.events = EventHub()
    app.state.start_guard = StartGuard()
    app.state.session_factory = async_session
    yield
    await app.state.places.aclose()


def create_app(settings: Settings) -> FastAPI:
    docs_enabled = settings.environment != "prod"
    app = FastAPI(
        title="Hangry API",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    app.state.settings = settings
    app.state.limiter = RateLimiter()
    api = APIRouter(prefix=API_PREFIX)
    api.include_router(sessions_router)
    api.include_router(groups_router)
    api.include_router(places_router)

    @api.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(api)
    # Last, because its catch-all route would otherwise shadow later routes.
    if settings.static_dir is not None:
        mount_frontend(app, settings.static_dir, api_prefix=API_PREFIX)

    return app


app = create_app(get_settings())
