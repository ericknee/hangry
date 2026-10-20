import { useEffect } from "react";
import { Navigate, generatePath, useNavigate, useParams } from "react-router-dom";
import LoadingScreen from "../../components/LoadingScreen";
import { ROUTES } from "../../routes";
import { clearParticipant, loadParticipantId } from "./groupStorage";
import LobbyScreen from "./LobbyScreen";
import ResultScreen from "./ResultScreen";
import SessionOver from "./SessionOver";
import VoteScreen from "./VoteScreen";
import WaitingScreen from "./WaitingScreen";
import { useGroupStatus } from "./useGroupStatus";

/**
 * The one page of a group session. What it shows follows the server's status, so a refresh or a
 * returning member lands on the right screen: lobby, voting, waiting for the others, or the result.
 */
export default function GroupSessionPage() {
  const { sessionId = "" } = useParams();
  const participantId = loadParticipantId(sessionId);
  if (!participantId) {
    return <Navigate to={generatePath(ROUTES.join, { sessionId })} replace />;
  }
  return <GroupSession sessionId={sessionId} participantId={participantId} />;
}

function GroupSession({ sessionId, participantId }: { sessionId: string; participantId: string }) {
  const navigate = useNavigate();
  const { status, error, apply, refresh } = useGroupStatus(sessionId, participantId);

  // A stored id the server doesn't know (another session's, or a purged one) is no use: forget it
  // and let the person join afresh.
  const forgotten = error?.status === 403;
  useEffect(() => {
    if (forgotten) {
      clearParticipant(sessionId);
      navigate(generatePath(ROUTES.join, { sessionId }), { replace: true });
    }
  }, [forgotten, sessionId, navigate]);

  if (error?.status === 404) return <SessionOver message="This session no longer exists." />;
  if (status === null || forgotten) return <LoadingScreen message="Loading your group..." />;

  const props = { sessionId, participantId, status, apply, refresh };
  switch (status.phase) {
    case "lobby":
      return <LobbyScreen {...props} />;
    case "swiping":
      return status.me.submitted ? <WaitingScreen {...props} /> : <VoteScreen {...props} />;
    case "done":
      return <ResultScreen {...props} />;
  }
}
