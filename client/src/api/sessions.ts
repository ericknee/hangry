export type SessionMode = "solo" | "group";

export interface LocationInput {
  place_id: string;
  lat: number;
  lng: number;
  formatted_address?: string | null;
}

export interface CandidateOut {
  place_id: string;
  name: string;
  address: string;
}

export interface CreateSessionResponse {
  session_id: string;
  mode: SessionMode;
  share_url: string | null;
  candidates: CandidateOut[];
}

export interface CreateSessionParams {
  mode: SessionMode;
  initialQuery: string;
  location?: LocationInput | null;
  radiusKm?: number | null;
}

export async function createSession(params: CreateSessionParams): Promise<CreateSessionResponse> {
  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mode: params.mode,
      initial_query: params.initialQuery,
      location: params.location ?? null,
      radius_km: params.radiusKm ?? null,
    }),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  return res.json();
}
