import { apiRequest } from "./http";
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
  return apiRequest<SearchResponse>(`/api/sessions/${encodeURIComponent(sessionId)}/search`, {
    method: "POST",
    body: {
      after: answers.after,
      price_levels: answers.priceLevels,
      dietary: answers.dietary,
      mode: answers.mode,
      minutes: answers.minutes,
    },
  });
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
  const { restaurants } = await apiRequest<{ restaurants: Restaurant[] }>(
    `/api/sessions/${encodeURIComponent(sessionId)}/results`,
  );
  return restaurants;
}

export async function createSession(params: CreateSessionParams): Promise<CreateSessionResponse> {
  return apiRequest<CreateSessionResponse>("/api/sessions", {
    method: "POST",
    body: {
      mode: params.mode,
      initial_query: params.initialQuery,
      location: params.location ?? null,
    },
  });
}
