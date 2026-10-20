import type { VoteValue } from "../../types";

// localStorage rather than sessionStorage: a member who closes the tab or follows the invite link
// again should get back in as the same person. Every access can throw (private mode, blocked
// storage), so each is wrapped and the flow works without it.

const credentialKey = (sessionId: string) => `hangry.participant.${sessionId}`;
const votesKey = (sessionId: string) => `hangry.votes.${sessionId}`;

/** This browser's member id for the session, or null if it hasn't joined. */
export function loadParticipantId(sessionId: string): string | null {
  try {
    return localStorage.getItem(credentialKey(sessionId));
  } catch {
    return null;
  }
}

export function saveParticipantId(sessionId: string, participantId: string): void {
  try {
    localStorage.setItem(credentialKey(sessionId), participantId);
  } catch {
    // Without storage the member can't come back after a refresh; this tab still works.
  }
}

export function clearParticipant(sessionId: string): void {
  try {
    localStorage.removeItem(credentialKey(sessionId));
    localStorage.removeItem(votesKey(sessionId));
  } catch {
    // Nothing to clear.
  }
}

/** The unsent votes of a member who refreshed mid-deck. */
export function loadVoteDraft(sessionId: string): Record<string, VoteValue> {
  try {
    const raw = localStorage.getItem(votesKey(sessionId));
    const parsed: unknown = raw ? JSON.parse(raw) : {};
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return {};
    return Object.fromEntries(
      Object.entries(parsed).filter(([, v]) => v === 1 || v === -1),
    ) as Record<string, VoteValue>;
  } catch {
    return {};
  }
}

export function saveVoteDraft(sessionId: string, votes: Record<string, VoteValue>): void {
  try {
    localStorage.setItem(votesKey(sessionId), JSON.stringify(votes));
  } catch {
    // The draft then lives only in page state.
  }
}
