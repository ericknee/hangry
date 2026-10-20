"""Display names for group members: generated when blank, made unique within a session."""

import random
from collections.abc import Iterable

NAME_MAX = 30  # matches participants.name

_ADJECTIVES = [
    "Hungry",
    "Peckish",
    "Starving",
    "Famished",
    "Crispy",
    "Saucy",
    "Spicy",
    "Zesty",
    "Cheesy",
    "Toasty",
]
_FOODS = [
    "Taco",
    "Noodle",
    "Dumpling",
    "Waffle",
    "Pickle",
    "Biscuit",
    "Burrito",
    "Pretzel",
    "Muffin",
    "Falafel",
]


def random_name() -> str:
    return f"{random.choice(_ADJECTIVES)} {random.choice(_FOODS)}"


def unique_name(requested: str | None, taken: Iterable[str]) -> str:
    """`requested` (or a generated name if blank), with " 2", " 3", ... added until no other member
    has it. Compared ignoring case, which is stricter than the database's unique constraint."""
    taken_lower = {name.lower() for name in taken}
    base = (requested or "").strip()[:NAME_MAX] or random_name()
    candidate = base
    number = 2
    while candidate.lower() in taken_lower:
        suffix = f" {number}"
        candidate = base[: NAME_MAX - len(suffix)] + suffix
        number += 1
    return candidate
