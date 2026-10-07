import { useState } from "react";
import type { SetupAnswers } from "../../types";
import { loadSetupAnswers, saveSetupAnswers } from "./setupAnswers";

/** Setup answers for one session, persisted to sessionStorage on every change. */
export function useSetupAnswers(sessionId: string) {
  const [answers, setAnswers] = useState(() => loadSetupAnswers(sessionId));

  function update(patch: Partial<SetupAnswers>) {
    const next = { ...answers, ...patch };
    setAnswers(next);
    saveSetupAnswers(sessionId, next);
  }

  return [answers, update] as const;
}
