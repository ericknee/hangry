export interface CityPrediction {
  place_id: string;
  description: string;
}

export interface CityLocation {
  place_id: string;
  lat: number;
  lng: number;
  formatted_address: string | null;
}

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
