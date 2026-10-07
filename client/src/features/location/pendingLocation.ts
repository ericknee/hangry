import type { PendingLocation } from "../../types";

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
