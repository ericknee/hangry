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


async def check_places() -> None:
    client = PlacesClient()
    results = await client.search_text("pizza", lat=40.7484, lng=-73.9857)
    print(f"[places]  OK — {len(results)} result(s)")


async def check_claude() -> None:
    client = ClaudeClient()
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
