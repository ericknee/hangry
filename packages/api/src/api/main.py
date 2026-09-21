from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import sessions

app = FastAPI(title="TableTalk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
