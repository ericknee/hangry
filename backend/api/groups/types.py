"""Request/response models for group sessions.

Participant ids are credentials, so no model here that other members can read contains one.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from api.places.types import PlaceId
from api.sessions.types import DisplayName, RestaurantOut

# Group sessions start in the lobby; the solo-only "setup" phase never applies to them.
GroupPhase = Literal["lobby", "swiping", "done"]

# The same limit as the solo craving: it is stored per member and deleted after 30 days.
Craving = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]

# The UI sends -1 or 1; larger magnitudes are reserved for future strengths (see VoteRecord).
MAX_VOTE_STRENGTH = 5
MAX_VOTES_PER_SUBMIT = 200  # 8 searches of up to 20 places each, before duplicates are dropped


class JoinRequest(BaseModel):
    name: DisplayName | None = None
    craving: Craving | None = None


class JoinResponse(BaseModel):
    participant_id: str
    name: str


class UpdateMemberRequest(BaseModel):
    """Lobby edits. Rejected with 409 once the host has started."""

    name: DisplayName | None = None
    craving: Craving | None = None


class MemberOut(BaseModel):
    """What other members see about a member. No id, no craving."""

    name: str
    is_host: bool
    # True once the member has submitted, or the host ended the session on their behalf.
    submitted: bool


class MeOut(BaseModel):
    name: str
    craving: str | None
    is_host: bool
    submitted: bool


class VoteIn(BaseModel):
    place_id: PlaceId
    # Positive like, negative dislike. 0 is written by the server for the members the host
    # ends early, never sent by a client.
    value: Annotated[int, Field(ge=-MAX_VOTE_STRENGTH, le=MAX_VOTE_STRENGTH)]

    @field_validator("value")
    @classmethod
    def _not_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("a vote is a like or a dislike")
        return value


class SubmitVotesRequest(BaseModel):
    """One vote for every place in the member's deck; the service rejects an incomplete deck."""

    votes: list[VoteIn] = Field(max_length=MAX_VOTES_PER_SUBMIT)


class PlaceTally(BaseModel):
    place_id: str
    score: int  # sum of vote values
    likes: int
    dislikes: int
    liked_by: list[str]  # display names
    disliked_by: list[str]


class GroupResult(BaseModel):
    winner: RestaurantOut
    # True when nobody liked anything, so the winner is just the top-ranked place.
    no_likes: bool
    # Every place, best first; the final screen decides how much of this to show.
    tallies: list[PlaceTally]


class GroupStatus(BaseModel):
    """The whole group state for one member. `GET .../group` returns it and the SSE stream pushes
    it on every change, so the client handles both the same way."""

    phase: GroupPhase
    me: MeOut
    members: list[MemberOut]
    result: GroupResult | None
