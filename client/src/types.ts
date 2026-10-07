import type { components } from "./api/types.gen";

type Schemas = components["schemas"];

// ── API types ─────────────────────────────────────────────────────────────────
// Generated from the backend's Pydantic types (backend/api/**/types.py). After changing those,
// run `npm run gen:api` in client/; a backend test fails if the committed output is stale.

export type SessionMode = Schemas["CreateSessionRequest"]["mode"];
export type LocationInput = Schemas["LocationInput"];
export type CreateSessionRequest = Schemas["CreateSessionRequest"];
export type CreateSessionResponse = Schemas["SessionResponse"];
export type SearchRequest = Schemas["SearchRequest"];
export type SearchResponse = Schemas["SearchResponse"];
export type Restaurant = Schemas["RestaurantOut"];
export type ResultsResponse = Schemas["ResultsResponse"];
export type CityPrediction = Schemas["CityPrediction"];
export type CityLocation = Schemas["CityLocation"];

// Setup option values, taken from the search request so they can't drift from the backend.
export type After = SearchRequest["after"];
export type Dietary = NonNullable<SearchRequest["dietary"]>;
export type TravelMode = SearchRequest["mode"];

// ── Client-only types ─────────────────────────────────────────────────────────

/** The location chosen on the first page, held until the session is created. */
export type PendingLocation = LocationInput;

/** Answers to the four setup questions, held in the browser until the search call. */
export interface SetupAnswers {
  after: After | null;
  // 1 = "$" ... 4 = "$$$$". Empty means any price.
  priceLevels: number[];
  dietary: Dietary;
  mode: TravelMode;
  minutes: number;
}

export interface CreateSessionParams {
  mode: SessionMode;
  initialQuery: string;
  location?: PendingLocation | null;
}
