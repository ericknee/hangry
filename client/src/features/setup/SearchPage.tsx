import { useState } from "react";
import { generatePath, useNavigate } from "react-router-dom";
import { userMessage } from "../../api/http";
import { createSession } from "../../api/sessions";
import Button from "../../components/Button";
import Page from "../../components/Page";
import TextInput from "../../components/TextInput";
import { useToast } from "../../components/useToast";
import { ROUTES } from "../../routes";
import { loadPendingLocation } from "../location/pendingLocation";

export default function SearchPage() {
  const navigate = useNavigate();
  const [craving, setCraving] = useState("");
  const { showError } = useToast();
  const [submitting, setSubmitting] = useState(false);

  async function handleNext() {
    setSubmitting(true);
    try {
      const session = await createSession({
        mode: "solo",
        initialQuery: craving.trim(),
        location: loadPendingLocation(),
      });
      navigate(generatePath(ROUTES.setupAfter, { sessionId: session.session_id }));
    } catch (error) {
      showError(userMessage(error, "Couldn't start your session. Try again."));
      setSubmitting(false);
    }
  }

  return (
    <Page>
      <h1 className="title text-center">
        What are you craving? <span className="font-normal text-muted">optional</span>
      </h1>
      <TextInput
        autoFocus
        className="text-center"
        placeholder="Sushi, something spicy, comfort food..."
        value={craving}
        onChange={(e) => setCraving(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !submitting) handleNext();
        }}
      />
      <Button disabled={submitting} className="mt-2" onClick={handleNext}>
        Next
      </Button>
    </Page>
  );
}
