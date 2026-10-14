import { useState } from "react";
import { generatePath, useNavigate } from "react-router-dom";
import { userMessage } from "../../api/http";
import { createSession } from "../../api/sessions";
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
    <main className="page">
      <div className="flex w-full max-w-md flex-col gap-4">
        <h1 className="text-center text-2xl font-semibold text-ink">
          What are you craving? <span className="font-normal text-muted">optional</span>
        </h1>
        <input
          autoFocus
          className="w-full rounded-2xl border border-line bg-surface px-4 py-4 text-center text-xl text-ink placeholder:text-muted focus:border-accent focus:outline-none"
          placeholder="Sushi, something spicy, comfort food..."
          value={craving}
          onChange={(e) => setCraving(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !submitting) handleNext();
          }}
        />
        <button
          type="button"
          disabled={submitting}
          className="btn-primary mt-2"
          onClick={handleNext}
        >
          Next
        </button>
      </div>
    </main>
  );
}
