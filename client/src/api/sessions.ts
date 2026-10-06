import type { PendingLocation } from "../lib/pendingLocation";
import type { SetupAnswers } from "../lib/setupAnswers";

export type SessionMode = "solo" | "group";

export interface CreateSessionResponse {
  session_id: string;
  mode: SessionMode;
  share_url: string | null;
}

export interface CreateSessionParams {
  mode: SessionMode;
  initialQuery: string;
  location?: PendingLocation | null;
}

export interface SearchResponse {
  count: number;
}

/** Sends the setup answers and runs the one restaurant search for this session. */
export async function searchSession(
  sessionId: string,
  answers: SetupAnswers,
): Promise<SearchResponse> {
  if (answers.after === null) throw new Error("Setup is incomplete: missing 'after'");
  const res = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      after: answers.after,
      price_levels: answers.priceLevels,
      dietary: answers.dietary,
      mode: answers.mode,
      minutes: answers.minutes,
    }),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export interface Restaurant {
  place_id: string;
  name: string;
  address: string;
  cuisine: string | null;
  rating: number | null;
  rating_count: number | null;
  price_level: number | null;
  distance_m: number | null;
  maps_uri: string | null;
}

/** All search results for the session, best first. Rejects if they expired or never existed. */
export async function getResults(sessionId: string): Promise<Restaurant[]> {
  const res = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/results`);
  if (!res.ok) throw new Error(`Results failed: ${res.status}`);
  return (await res.json()).restaurants;
}

export async function createSession(params: CreateSessionParams): Promise<CreateSessionResponse> {
  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mode: params.mode,
      initial_query: params.initialQuery,
      location: params.location ?? null,
    }),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  return res.json();
}
