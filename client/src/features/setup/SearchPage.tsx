import { useState } from "react";
import { generatePath, useNavigate, useSearchParams } from "react-router-dom";
import { userMessage } from "../../api/http";
import { createSession } from "../../api/sessions";
import Button from "../../components/Button";
import Page from "../../components/Page";
import TextInput from "../../components/TextInput";
import { useToast } from "../../components/useToast";
import { ROUTES } from "../../routes";
import { saveParticipantId } from "../group/groupStorage";
import { loadPendingLocation } from "../location/pendingLocation";

const MAX_CRAVING_LENGTH = 100; // matches the backend limit on initial_query
const MAX_NAME_LENGTH = 30; // matches the backend limit on display names

export default function SearchPage() {
  const navigate = useNavigate();
  // "Plan with friends" arrives as /search?mode=group; the URL keeps it across a refresh.
  const isGroup = useSearchParams()[0].get("mode") === "group";
  const [craving, setCraving] = useState("");
  const [name, setName] = useState("");
  const { showError } = useToast();
  const [submitting, setSubmitting] = useState(false);

  async function handleNext() {
    if (submitting) return;
    setSubmitting(true);
    try {
      const session = await createSession({
        mode: isGroup ? "group" : "solo",
        initialQuery: craving.trim(),
        location: loadPendingLocation(),
        name,
      });
      // The host's id is what later proves they are the host; the setup pages tell a group from a
      // solo session by it.
      if (session.participant_id) saveParticipantId(session.session_id, session.participant_id);
      navigate(generatePath(ROUTES.setupAfter, { sessionId: session.session_id }));
    } catch (error) {
      showError(userMessage(error, "Couldn't start your session. Try again."));
      setSubmitting(false);
    }
  }

  return (
    <Page>
      {isGroup && (
        <TextInput
          className="text-center"
          aria-label="Your name"
          placeholder="Your name (optional)"
          maxLength={MAX_NAME_LENGTH}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      )}
      <h1 className="title text-center">
        What are you craving? <span className="font-normal text-muted">optional</span>
      </h1>
      <TextInput
        autoFocus={!isGroup}
        className="text-center"
        placeholder="Sushi, something spicy, comfort food..."
        maxLength={MAX_CRAVING_LENGTH}
        value={craving}
        onChange={(e) => setCraving(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !submitting) handleNext();
        }}
      />
      <Button aria-busy={submitting} className="mt-2" onClick={handleNext}>
        {submitting ? "Loading..." : "Next"}
      </Button>
    </Page>
  );
}
