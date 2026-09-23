"""Present node.

Takes the top-scoring candidates and attaches a plain-language explanation
of why the shortlist fits everyone, not just the average member.
"""

from __future__ import annotations

from agent.clients.claude import ClaudeClient
from agent.state import HangryState

_claude: ClaudeClient | None = None

SHORTLIST_SIZE = 3


def _get_claude() -> ClaudeClient:
    global _claude
    if _claude is None:
        _claude = ClaudeClient()
    return _claude


async def present_shortlist(state: HangryState) -> HangryState:
    shortlist = state["candidates"][:SHORTLIST_SIZE]
    state["shortlist"] = shortlist

    if shortlist:
        state["explanation"] = await _get_claude().explain_shortlist(
            candidates=shortlist, members=state["members"]
        )
    return state
