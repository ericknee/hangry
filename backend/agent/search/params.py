"""Turn the setup answers into Places Text Search parameters. Pure functions, no I/O."""

from __future__ import annotations

from agent.types import SearchParams

# Straight-line metres covered per minute: speed divided by a detour factor,
# because roads are longer than the crow-flies distance.
WALK_M_PER_MIN = 80
DRIVE_M_PER_MIN = 500
DETOUR_FACTOR = 1.3

# after -> (default query text, place type filter or None)
_MEALS: dict[str, tuple[str, str | None]] = {
    "breakfast": ("breakfast", "breakfast_restaurant"),
    "lunch": ("lunch", "restaurant"),
    "dinner": ("dinner", "restaurant"),
    "coffee_dessert": ("coffee dessert", None),
    "drinks": ("drinks", "bar"),
}

# dietary -> (default query text, place type filter)
_DIETARY: dict[str, tuple[str, str]] = {
    "vegetarian": ("vegetarian restaurants", "vegetarian_restaurant"),
    "vegan": ("vegan restaurants", "vegan_restaurant"),
    "halal": ("halal restaurants", "halal_restaurant"),
}

_PRICE_LEVELS = {
    1: "PRICE_LEVEL_INEXPENSIVE",
    2: "PRICE_LEVEL_MODERATE",
    3: "PRICE_LEVEL_EXPENSIVE",
    4: "PRICE_LEVEL_VERY_EXPENSIVE",
}


def radius_m(mode: str, minutes: int) -> int:
    speed = WALK_M_PER_MIN if mode == "walk" else DRIVE_M_PER_MIN
    return round(minutes * speed / DETOUR_FACTOR)


def build_search_params(
    *,
    after: str,
    dietary: str,
    craving: str,
    price_levels: list[int],
    mode: str,
    minutes: int,
) -> SearchParams:
    """The search takes one place type, and dietary wins it (strict).

    The query is the craving if given, otherwise the default text for whichever type won.
    """
    default_query, included_type = _DIETARY.get(dietary) or _MEALS[after]

    return SearchParams(
        query=craving.strip() or default_query,
        included_type=included_type,
        price_levels=[_PRICE_LEVELS[level] for level in sorted(set(price_levels))],
        radius_m=radius_m(mode, minutes),
    )
