import { useState } from "react";
import { Navigate, generatePath, useNavigate, useParams } from "react-router-dom";
import { joinSession } from "../../api/groups";
import { ApiError, userMessage } from "../../api/http";
import Button from "../../components/Button";
import Page from "../../components/Page";
import TextInput from "../../components/TextInput";
import { useToast } from "../../components/useToast";
import { ROUTES } from "../../routes";
import { loadParticipantId, saveParticipantId } from "./groupStorage";

const MAX_NAME_LENGTH = 30; // matches the backend limit on display names
const MAX_CRAVING_LENGTH = 100; // matches the backend limit on cravings

function joinMessage(error: unknown): string {
  const fallback = userMessage(error, "Couldn't join. Please try again.");
  if (error instanceof ApiError && error.status === 409) {
    return "This session has already started or is full.";
  }
  if (error instanceof ApiError && error.status === 404) {
    return "We couldn't find that session. Check the link and try again.";
  }
  return fallback;
}

/** The invite link's page: pick a name and craving, then wait in the lobby. */
export default function JoinPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const { showError } = useToast();
  const [name, setName] = useState("");
  const [craving, setCraving] = useState("");
  const [joining, setJoining] = useState(false);

  // Following the link again as the same member (or the host, who is already in) goes straight in.
  if (loadParticipantId(sessionId)) {
    return <Navigate to={generatePath(ROUTES.group, { sessionId })} replace />;
  }

  async function handleJoin() {
    if (joining) return;
    setJoining(true);
    try {
      const member = await joinSession(sessionId, {
        name: name.trim() || null,
        craving: craving.trim() || null,
      });
      saveParticipantId(sessionId, member.participant_id);
      navigate(generatePath(ROUTES.group, { sessionId }));
    } catch (error) {
      showError(joinMessage(error));
      setJoining(false);
    }
  }

  return (
    <Page gap="gap-6">
      <h1 className="title-lg">You&apos;re invited to pick a restaurant</h1>
      <label className="flex flex-col gap-2 text-ink">
        <span className="font-semibold">
          Your name <span className="font-normal text-muted">optional</span>
        </span>
        <TextInput
          placeholder="We'll pick one if you leave it blank"
          maxLength={MAX_NAME_LENGTH}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </label>
      <label className="flex flex-col gap-2 text-ink">
        <span className="font-semibold">
          What are you craving? <span className="font-normal text-muted">optional</span>
        </span>
        <TextInput
          placeholder="Sushi, something spicy, comfort food..."
          maxLength={MAX_CRAVING_LENGTH}
          value={craving}
          onChange={(e) => setCraving(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void handleJoin();
          }}
        />
      </label>
      <Button aria-busy={joining} className="mt-2" onClick={handleJoin}>
        {joining ? "Joining..." : "Join"}
      </Button>
    </Page>
  );
}
