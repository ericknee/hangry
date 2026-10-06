# Filtering plan: LLM-free v1

Status: the solo MVP is built (see "Implementation status" and "Decided for v1" below). The sections
before "Decided for v1" are the original plan: group sessions, the LangGraph graph and aggregation
strategies mentioned there were removed from the code as unused and remain in git history.

## Goals

- As simple as possible for the user: few taps, few options, no typing.
- No LLM in v1. Claude client, `anthropic_api_key` setting and dependency are removed.
- Rankings matter, so use the Google Places **Enterprise** tier (no Atmosphere).

## Decisions

- **Places tier:** Enterprise Text Search, about $35 per 1,000 requests (1,000 free/month). Pro would be $32 but has no rating, price or hours.
- **One search per session.** Each extra page or query is another billed request.
- **No finalist detail fetch.** Enterprise search already returns what it would have fetched.
- **No Atmosphere tier** ($40/1,000). Dietary is handled with place types instead.
- Pricing figures came from Google's pricing and field pages via a page summarizer. Verify on the official pages and with one real call before budgeting. The existing `SEARCH_FIELD_MASK` comment calling it "Essentials" is probably wrong (Pro for Text Search).

## Flow

```
setup (hard filters) -> search (Enterprise, filtered) -> vetoes (adaptive) -> aggregate -> present 3
```

1. **Setup, asked once per member, ~3 taps:** price range, dietary need, distance.
2. **Search:** one Text Search with server-side filters (below).
3. **Vetoes:** adaptive "anything you'd skip?" questions, only over attributes that split the results. Max 3, stop at <=3 candidates.
4. **Aggregate:** vetoes remove candidates per member; `maximin` for groups.
5. **Present:** 3 picks, top one highlighted, templated one-line reason, "Open in Maps" link.

### Location and distance

- Distance is not a setup question. It is asked as **"How far are you willing to travel?"** in minutes, with mode folded into each option (e.g. 5 / 15 min walk, 10 / 20 min drive).
- Radius = minutes x speed / 1.3 detour factor. Walk ~80 m/min, drive ~500 m/min (30 km/h), so about 60 m and 385 m of straight-line radius per minute. These are estimates; tune in a real city. No API call.
- The radius feeds the existing `_bounding_box` directly. **No trimming to a circle**: corners are about 1.4x farther than the stated time, accepted for v1 (could shrink the half-side to ~0.85x later).
- **Current location:** a "Current location" entry in the dropdown when the location search bar is focused, using the browser Geolocation API. Free, needs HTTPS (localhost OK) and a permission tap. It skips city autocomplete and the city lookup, so it is cheaper than typing a city. Typed-city autocomplete stays as the fallback if permission is denied.
- No reverse geocoding (paid); show "Using your location". Do not store raw coordinates in `SessionRecord`; coordinates are stored rounded to 3 decimals (~110 m), and the search reads that stored copy.
- **Groups (not for v1):** search is centered on the **host's location**; the radius is the smallest any member chose. The host shares the session with others only **after the initial screen is completed**.

Solo is the same graph with one member. Groups use the strictest filters: lowest max price, all dietary needs, shortest distance.

## Search filters (Text Search request parameters)

| Filter | Use |
|---|---|
| `openNow=true` | Fixed default |
| `minRating=3.5` | Fixed default; retry at 3.0 if results are thin (one extra billed request) |
| `priceLevels` | From setup |
| `includedType` + `strictTypeFiltering` | One type only (e.g. `vegan_restaurant`, `vegetarian_restaurant`, `halal_restaurant`); cannot OR types |
| `locationRestriction` | Rectangle around the city point; trim to a true circle afterwards by distance |
| `rankPreference` | Relevance by default |
| `pageSize` | 20 (max 60 results across pages, each page billed) |

Caveats: a single `includedType` means conflicting group dietary needs (e.g. vegan + halal) need post-filtering or a text query. Pre-filtering removes the questions it answers, so price is asked in setup, not as a veto.

## Enterprise fields used

`displayName`, `formattedAddress`, `location`, `types`, `primaryType`, `primaryTypeDisplayName`, `businessStatus`, `googleMapsUri`, `photos`, `rating`, `userRatingCount`, `priceLevel`, opening hours.

## Ranking

Rating adjusted for review count (so 5 stars from 3 reviews does not beat 4.6 from 800), after vetoes. Distance as a tiebreak.

## Cost estimate (one Enterprise search per session)

| Sessions/month | Enterprise | Pro |
|---|---|---|
| 1,000 | $0 | $0 |
| 10,000 | ~$315 | ~$160 |
| 100,000 | ~$3,465 | ~$3,040 |

Caching candidates by area for a few hours could cut volume below one search per session. Check Google's terms on storing Places data first; `place_id` is explicitly storable.

## Implementation status

- [x] Places client: Enterprise field mask and filter params (`clients/places.py`)
- [x] Query building, retrieval with retry, ranking (`search_params.py`, `retrieval.py`, `ranking.py`)
- [x] Search and results endpoints, in-memory candidate cache, session recording, Alembic
- [x] Frontend: location, craving, four setup pages, loading screen, swipeable shortlist
- [x] Removed the unused LangGraph graph, aggregation strategies, Claude client, websocket manager,
      old question pages, smoke test, and their dependencies and settings
- [ ] Cuisine veto step (`questions.py` selection logic exists; no endpoint or page)
- [ ] Verification against live Google Places and Postgres

## Decided for v1 (solo only; no invite option)

Pages: location (`/`) -> optional craving (`/search`, creates session) -> setup questions -> search -> cuisine veto -> results.

- **Setup questions:**
  - What are you after? Single-select: Breakfast, Lunch, Dinner, Coffee & dessert, Drinks.
  - Price: multi-select range of tiers; nothing selected means any price.
  - Dietary: single-select: None, Vegetarian, Vegan, Halal.
  - Travel: a Walking / Driving choice, plus "how far are you willing to travel?" in minutes as a slider, 5 to 60 in steps of 5, default 20. The user is never asked for speeds; speeds are an internal assumption.
- **Fixed filters:** open now; minimum rating 3.5; retry once at 3.0 if results are thin.
- **Request shape:** the browser keeps the setup answers and sends them in **one call** after the last setup page, with a loading screen while the search runs.
- **Veto question:** one cuisine veto (adaptive) after the search returns, before results.
- **Ranking:** rating weighted by review count; show 3; distance as tiebreak.
- **Results:** no Google photos for now (a separate billed request; may change later). Empty or failed search shows empty results with an error message.
- **"What are you after?" mapping:** Breakfast = `breakfast_restaurant`, Lunch and Dinner = `restaurant`, Drinks = `bar`; Coffee & dessert has no type filter and uses the text query "coffee dessert" instead.
- **Query text:** the craving if typed, otherwise the default text for whichever place type wins the single type filter. Dietary wins the type (vegan/vegetarian/halal -> "vegan restaurants" etc.), so the meal then only shapes the search through open-now.
- **Speeds (internal):** walk 80 m/min, drive 500 m/min, divided by a 1.3 detour factor for the straight-line radius. Square bounding box, no circle trim.
- **Layout:** one setup question per page.
- **Database setup:** Alembic scaffolded now (not `create_all`); `database_url` becomes a required setting.
- **Database:** sessions are recorded in Postgres (`SessionRecord`). A row is inserted at session creation (location, craving), then updated with the setup answers, the results and the final pick. Coordinates are rounded to 3 decimals (about 110 m) before storing; the search uses the stored copy.

## Future improvements

- **Session survives a refresh:** save session details (location, craving, setup answers) to the database as they are entered, so a refresh mid-flow resumes instead of restarting. v1 keeps answers in the browser and sends them in one call.
- Group sessions with invites, the join page, and host-location search (see above).
- Google photos on results.
- Caching candidates by area to cut search volume.

## Open questions

- Should group hard filters be anonymous (only the combined result is shown)? (Group is out of v1.)
- If the host completes the initial screen before sharing, when do other members' price and dietary answers apply? Option: the search runs after all members finish setup, so strictest-filter-wins still works. (Group is out of v1.)
- Candidate questions beyond the v1 set: see below.

## Candidate questions

Each must map to data we already get from the one search (types, price, rating, review count, hours, distance) or to a ranking tweak. No extra API calls.

| Question | Taps | Maps to | Role | Value |
|---|---|---|---|---|
| **What are you after?** Breakfast / Lunch / Dinner / Coffee & dessert / Drinks | 5 options | `includedType` (`breakfast_restaurant`, `brunch_restaurant`, `cafe`, `dessert_shop`, `bar`) or `restaurant` | Setup filter | High: replaces the generic "restaurant" query and sets the whole candidate pool |
| **Quick bite or sit-down?** | 2 | Types: fast food, sandwich, taco, deli vs. restaurant, bistro, steak house | Setup filter or veto | High: very natural, strong split |
| **Familiar or adventurous?** | 2 | Ranking: popular (high review count) vs. hidden gem (high rating, fewer reviews) | Ranking tilt, not a filter | Medium-high: no candidates removed, one tap |
| **Occasion:** casual / date / celebration | 3 | Types (`fine_dining_restaurant`, `wine_bar`, `bistro`) plus price | Veto or ranking | Medium: overlaps with price |
| **Drinks involved?** | 2 | Types: `bar`, `pub`, `wine_bar`, `brewery`, `cocktail_bar` | Veto | Medium: useful for groups |
| **This or that** (two cuisine cards) | 1 tap each | Cuisine veto, shown as a pair | Veto | Medium: faster than a 5-option list |

Not feasible without Atmosphere or extra calls: dine-in vs. takeout, outdoor seating, kid-friendly, reservations, noise level, spice level, chain vs. local (only hackable by name duplication).

### Suggested v1 set

- Setup (3 taps): **what are you after?**, price, dietary. Distance becomes a default radius rather than a question, unless testing shows it matters.
- Adaptive: cuisine veto, then **quick bite or sit-down** if it splits the results.
- No question for familiar vs. adventurous: ship it as a fixed ranking default (rating weighted by review count) and revisit.

Deferred: occasion, drinks, this-or-that.
