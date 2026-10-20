import type {
  GroupStatus,
  JoinRequest,
  JoinResponse,
  MeOut,
  SearchRequest,
  SearchResponse,
  SetupAnswers,
  SubmitVotesRequest,
  UpdateMemberRequest,
  VoteValue,
} from "../types";
import { apiRequest } from "./http";

const base = (sessionId: string) => `/api/sessions/${encodeURIComponent(sessionId)}`;

/** The participant id is the credential; REST calls send it in this header. */
const asMember = (participantId: string) => ({ "X-Participant-Id": participantId });

export function joinSession(sessionId: string, body: JoinRequest): Promise<JoinResponse> {
  return apiRequest<JoinResponse>(`${base(sessionId)}/join`, { method: "POST", body });
}

export function updateMe(
  sessionId: string,
  participantId: string,
  body: UpdateMemberRequest,
): Promise<MeOut> {
  return apiRequest<MeOut>(`${base(sessionId)}/me`, {
    method: "PATCH",
    body,
    headers: asMember(participantId),
  });
}

export function getGroupStatus(sessionId: string, participantId: string): Promise<GroupStatus> {
  return apiRequest<GroupStatus>(`${base(sessionId)}/group`, { headers: asMember(participantId) });
}

/** Host only: runs the searches and opens voting. `count` 0 means the lobby stays open. */
export function startGroupSession(
  sessionId: string,
  participantId: string,
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
  return apiRequest<SearchResponse>(`${base(sessionId)}/start`, {
    method: "POST",
    body,
    headers: asMember(participantId),
  });
}

/** One vote for every place in the deck. Not retried: a repeat would be refused as a second submit. */
export function submitVotes(
  sessionId: string,
  participantId: string,
  votes: Record<string, VoteValue>,
): Promise<GroupStatus> {
  const body: SubmitVotesRequest = {
    votes: Object.entries(votes).map(([place_id, value]) => ({ place_id, value })),
  };
  return apiRequest<GroupStatus>(`${base(sessionId)}/votes`, {
    method: "POST",
    body,
    headers: asMember(participantId),
  });
}

/** Host only: ends voting now; members who haven't submitted get no votes. */
export function endGroupSession(sessionId: string, participantId: string): Promise<GroupStatus> {
  return apiRequest<GroupStatus>(`${base(sessionId)}/end`, {
    method: "POST",
    headers: asMember(participantId),
  });
}

/** The live status stream. The browser can't set headers on it, so the id goes in the query. */
export function groupEventsUrl(sessionId: string, participantId: string): string {
  return `${base(sessionId)}/events?participant_id=${encodeURIComponent(participantId)}`;
}
