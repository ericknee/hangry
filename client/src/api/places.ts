import type { CityLocation, CityPrediction } from "../types";

export async function autocompleteCities(input: string): Promise<CityPrediction[]> {
  const res = await fetch(`/api/places/autocomplete?input=${encodeURIComponent(input)}`);
  if (!res.ok) throw new Error(`Autocomplete failed: ${res.status}`);
  return res.json();
}

export async function getCityLocation(placeId: string): Promise<CityLocation> {
  const res = await fetch(`/api/places/cities/${encodeURIComponent(placeId)}`);
  if (!res.ok) throw new Error(`City lookup failed: ${res.status}`);
  return res.json();
}
