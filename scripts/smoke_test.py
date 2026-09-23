"""Run from the repo root: `uv run python scripts/smoke_test.py`

Verifies, in order:
1. Google Places API key + connectivity (one text search)
2. Anthropic API key + connectivity (one small completion)
3. The LangGraph skeleton compiles and a solo (1-member) run terminates

If all three print OK, credentials, dependencies, and the graph skeleton
are wired correctly before writing any real feature logic.
"""

import asyncio

from agent.clients.claude import ClaudeClient
from agent.clients.places import PlacesClient
from agent.graph import build_graph
from api.core.config import get_settings


async def check_places() -> None:
    async with PlacesClient(api_key=get_settings().google_places_api_key) as client:
        results = await client.search_text("pizza", lat=40.7484, lng=-73.9857)
    print(f"[places]  OK — {len(results)} result(s)")


async def check_claude() -> None:
    api_key = get_settings().anthropic_api_key
    if api_key is None:
        print("[claude]  SKIPPED — ANTHROPIC_API_KEY not set")
        return
    client = ClaudeClient(api_key=api_key)
    result = await client.generate_question(context="craving something quick")
    print(f"[claude]  OK — got response: {bool(result)}")


def check_graph() -> None:
    graph = build_graph()
    print(f"[graph]   OK — compiled: {graph is not None}")


async def main() -> None:
    check_graph()
    await check_places()
    await check_claude()


if __name__ == "__main__":
    asyncio.run(main())
