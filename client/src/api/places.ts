import type { CityLocation, CityPrediction } from "../types";

/** `sessionToken` ties these requests and the city lookup into one Google billing session. */
export async function autocompleteCities(input: string, sessionToken: string): Promise<CityPrediction[]> {
  const res = await fetch(
    `/api/places/autocomplete?input=${encodeURIComponent(input)}&session_token=${sessionToken}`,
  );
  if (!res.ok) throw new Error(`Autocomplete failed: ${res.status}`);
  return res.json();
}

/** Ends the autocomplete session `sessionToken` belongs to. */
export async function getCityLocation(placeId: string, sessionToken: string): Promise<CityLocation> {
  const res = await fetch(
    `/api/places/cities/${encodeURIComponent(placeId)}?session_token=${sessionToken}`,
  );
  if (!res.ok) throw new Error(`City lookup failed: ${res.status}`);
  return res.json();
}
