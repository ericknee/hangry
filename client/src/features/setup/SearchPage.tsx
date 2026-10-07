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
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 via-blue-100 to-blue-200 p-6">
      <div className="flex w-full max-w-md flex-col gap-4">
        <h1 className="text-center text-2xl font-medium text-blue-950">
          What are you craving? <span className="font-normal text-blue-300">optional</span>
        </h1>
        <input
          autoFocus
          className="w-full bg-transparent text-center text-xl text-blue-900 placeholder:text-blue-300 focus:outline-none"
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
          className="mt-2 w-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400 py-4 font-medium text-white shadow-md transition-opacity hover:opacity-90 disabled:opacity-60"
          onClick={handleNext}
        >
          Next
        </button>
      </div>
    </main>
  );
}
