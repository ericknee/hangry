import type {
  CreateSessionParams,
  CreateSessionRequest,
  CreateSessionResponse,
  ResultsResponse,
  Restaurant,
  SearchRequest,
  SearchResponse,
  SetupAnswers,
} from "../types";
import { apiRequest } from "./http";

/**
 * Sends the setup answers and runs the one restaurant search for this session.
 * Safe to retry: the server returns the cached results for a repeat call instead of searching again.
 */
export async function searchSession(
  sessionId: string,
  answers: SetupAnswers,
): Promise<SearchResponse> {
  if (answers.after === null) throw new Error("Setup is incomplete: missing 'after'");
  const body: SearchRequest = {
    after: answers.after,
    price_levels: answers.priceLevels,
    dietary: answers.dietary,
    mode: answers.mode,
    minutes: answers.minutes,
  };
  return apiRequest<SearchResponse>(`/api/sessions/${encodeURIComponent(sessionId)}/search`, {
    method: "POST",
    body,
    retry: true,
  });
}

/** All search results for the session, best first. Rejects if they expired or never existed. */
export async function getResults(sessionId: string): Promise<Restaurant[]> {
  const { restaurants } = await apiRequest<ResultsResponse>(
    `/api/sessions/${encodeURIComponent(sessionId)}/results`,
  );
  return restaurants;
}

/** URL of a restaurant's photo, served by the backend proxy (the Google key stays server-side). */
export function photoUrl(sessionId: string, placeId: string): string {
  return `/api/sessions/${encodeURIComponent(sessionId)}/restaurants/${encodeURIComponent(placeId)}/photo`;
}

export async function createSession(params: CreateSessionParams): Promise<CreateSessionResponse> {
  const body: CreateSessionRequest = {
    mode: params.mode,
    initial_query: params.initialQuery,
    location: params.location ?? null,
  };
  return apiRequest<CreateSessionResponse>("/api/sessions", { method: "POST", body });
}
