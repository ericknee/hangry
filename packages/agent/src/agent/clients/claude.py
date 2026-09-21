"""Thin wrapper around the Anthropic SDK for the two LLM jobs in this graph:

1. Generating an adaptive elicitation question + its 3-5 tap options
2. Writing the one-line-per-candidate shortlist reasoning / group explanation

Kept deliberately small: the LLM's job here is generation, not open-ended
parsing (see the doc's "Elicitation UI" design decision) — options are
tapped, not typed, so there is no free-text NLU surface to cover.
"""

from __future__ import annotations

import os

from anthropic import AsyncAnthropic

MODEL = "claude-sonnet-4-6"


class ClaudeClient:
    def __init__(self, api_key: str | None = None) -> None:
        self._client = AsyncAnthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    async def generate_question(self, *, context: str) -> dict:
        """Return {"question": str, "options": [str, ...]} given elicitation context."""
        resp = await self._client.messages.create(
            model=MODEL,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Given this restaurant-preference context, propose ONE next "
                        "elicitation question with 3-5 short tap-able answer options. "
                        f"Context:\n{context}\n\n"
                        'Respond as JSON: {"question": "...", "options": ["...", ...]}'
                    ),
                }
            ],
        )
        # NOTE: swap in structured output / tool-use once this leaves the stub stage.
        return {"raw": resp.content}

    async def explain_shortlist(self, *, candidates: list[dict], members: list[dict]) -> str:
        """Return a plain-language explanation of why the shortlist fits everyone."""
        resp = await self._client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Explain in 2-3 sentences why this restaurant shortlist fits "
                        f"this group, not just the average member.\nCandidates: {candidates}\n"
                        f"Members: {members}"
                    ),
                }
            ],
        )
        return "".join(block.text for block in resp.content if block.type == "text")
