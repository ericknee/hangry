"""Counting a group's votes into a ranked list of places."""

from collections.abc import Iterable, Sequence

from api.types.groups_types import PlaceTally


def tally_votes(
    votes: Iterable[tuple[str, str, int]], ranked_place_ids: Sequence[str]
) -> list[PlaceTally]:
    """One entry per place, best first: highest total of vote values, ties broken by the search
    ranking. `votes` is (member name, place id, value); a value of 0 (no vote) counts for nothing
    and names nobody."""
    liked: dict[str, list[str]] = {place_id: [] for place_id in ranked_place_ids}
    disliked: dict[str, list[str]] = {place_id: [] for place_id in ranked_place_ids}
    score: dict[str, int] = dict.fromkeys(ranked_place_ids, 0)
    for name, place_id, value in votes:
        if place_id not in score or value == 0:
            continue
        score[place_id] += value
        (liked if value > 0 else disliked)[place_id].append(name)

    order = sorted(range(len(ranked_place_ids)), key=lambda i: (-score[ranked_place_ids[i]], i))
    return [
        PlaceTally(
            place_id=ranked_place_ids[i],
            score=score[ranked_place_ids[i]],
            likes=len(liked[ranked_place_ids[i]]),
            dislikes=len(disliked[ranked_place_ids[i]]),
            liked_by=liked[ranked_place_ids[i]],
            disliked_by=disliked[ranked_place_ids[i]],
        )
        for i in order
    ]
