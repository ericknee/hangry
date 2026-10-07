from agent.search.params import build_search_params, radius_m


def params(**overrides):
    base = dict(
        after="dinner", dietary="none", craving="", price_levels=[], mode="drive", minutes=20
    )
    return build_search_params(**{**base, **overrides})


def test_radius_minutes_to_metres():
    assert radius_m("walk", 5) == 308  # 5 * 80 / 1.3
    assert radius_m("drive", 20) == 7692  # 20 * 500 / 1.3


def test_default_query_and_type_per_meal():
    assert (params(after="breakfast").query, params(after="breakfast").included_type) == (
        "breakfast",
        "breakfast_restaurant",
    )
    p = params(after="coffee_dessert")
    assert (p.query, p.included_type) == ("coffee dessert", None)
    assert params(after="drinks").included_type == "bar"


def test_craving_replaces_default_query():
    assert params(craving="  spicy ramen ").query == "spicy ramen"


def test_dietary_takes_the_type_and_its_default_query():
    p = params(after="breakfast", dietary="vegan")
    assert (p.included_type, p.query) == ("vegan_restaurant", "vegan restaurants")
    assert params(dietary="halal").query == "halal restaurants"


def test_craving_still_wins_the_query_when_dietary_applies():
    p = params(after="lunch", dietary="halal", craving="kebab")
    assert (p.included_type, p.query) == ("halal_restaurant", "kebab")


def test_price_levels_mapped_and_sorted():
    assert params(price_levels=[3, 1, 3]).price_levels == [
        "PRICE_LEVEL_INEXPENSIVE",
        "PRICE_LEVEL_EXPENSIVE",
    ]


def test_dietary_goes_in_the_query_for_drinks_and_coffee():
    p = params(after="drinks", dietary="vegan")
    assert (p.included_type, p.query) == ("bar", "vegan drinks")
    p = params(after="coffee_dessert", dietary="halal")
    assert (p.included_type, p.query) == (None, "halal coffee dessert")
