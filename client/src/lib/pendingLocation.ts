/** Location chosen on the first page, held until the session is created on a later page. */
export interface PendingLocation {
  // Absent for "Current location", which comes from the browser, not Places.
  place_id?: string;
  lat: number;
  lng: number;
  formatted_address?: string | null;
}

const KEY = "hangry.pendingLocation";

export function savePendingLocation(location: PendingLocation | null): void {
  try {
    if (location) sessionStorage.setItem(KEY, JSON.stringify(location));
    else sessionStorage.removeItem(KEY);
  } catch {
    // Storage can be unavailable (private mode); the later page falls back to no location.
  }
}

export function loadPendingLocation(): PendingLocation | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as PendingLocation) : null;
  } catch {
    return null;
  }
}
