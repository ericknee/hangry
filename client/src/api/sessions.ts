export type SessionMode = "solo" | "group";

export interface CreateSessionResponse {
  session_id: string;
  mode: SessionMode;
  share_url: string | null;
}

export async function createSession(
  mode: SessionMode,
  initialQuery: string
): Promise<CreateSessionResponse> {
  const res = await fetch("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, initial_query: initialQuery }),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  return res.json();
}
