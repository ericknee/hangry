import type { CityLocation, CityPrediction } from "../types";
import { apiRequest } from "./http";

/**
 * `sessionToken` ties these requests and the city lookup into one Google billing session.
 * No retries: this fires on every debounced keystroke, so a retry would only answer a stale query.
 */
export function autocompleteCities(input: string, sessionToken: string): Promise<CityPrediction[]> {
  return apiRequest<CityPrediction[]>(
    `/api/places/autocomplete?input=${encodeURIComponent(input)}&session_token=${sessionToken}`,
    { retry: false },
  );
}

/** Ends the autocomplete session `sessionToken` belongs to. */
export function getCityLocation(placeId: string, sessionToken: string): Promise<CityLocation> {
  return apiRequest<CityLocation>(
    `/api/places/cities/${encodeURIComponent(placeId)}?session_token=${sessionToken}`,
  );
}
