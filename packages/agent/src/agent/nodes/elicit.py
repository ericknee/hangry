"""Elicitation node.

Runs once per member via LangGraph's `Send` API so members are elicited in
parallel branches — nobody blocks on anybody else. Each call asks at most
one adaptive follow-up question, chosen (eventually) by expected information
gain against the current candidate set; skips the question entirely once a
member's `elicitation_done` flag is set.
"""

from __future__ import annotations

from agent.clients.claude import ClaudeClient
from agent.state import MemberState

_claude: ClaudeClient | None = None


def _get_claude() -> ClaudeClient:
    global _claude
    if _claude is None:
        _claude = ClaudeClient()
    return _claude


async def elicit_member(member: MemberState) -> MemberState:
    if member["elicitation_done"]:
        return member

    context = "\n".join(p.get("question_text", "") for p in member["preferences"])
    # TODO: replace with a real expected-information-gain stopping rule.
    _question = await _get_claude().generate_question(context=context or "no preferences yet")

    # Stub: mark done after one round until the real stopping rule lands.
    member["elicitation_done"] = True
    return member
