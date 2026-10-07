import { useState } from "react";
import { generatePath, useNavigate, useParams } from "react-router-dom";
import { userMessage } from "../../api/http";
import { searchSession } from "../../api/sessions";
import { useToast } from "../../components/useToast";
import LoadingScreen from "../../components/LoadingScreen";
import OptionChips from "../../components/OptionChips";
import SetupStep from "./SetupStep";
import { ROUTES } from "../../routes";
import type { TravelMode } from "../../types";
import { MAX_MINUTES, MIN_MINUTES, MINUTES_STEP } from "./setupAnswers";
import { useSetupAnswers } from "./useSetupAnswers";

const MODE_OPTIONS: { value: TravelMode; label: string }[] = [
  { value: "walk", label: "Walking" },
  { value: "drive", label: "Driving" },
];

const SEARCH_ERROR = "Couldn't search for restaurants. Please try again.";

export default function TravelPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const [answers, update] = useSetupAnswers(sessionId);
  const { showError } = useToast();
  const [searching, setSearching] = useState(false);

  async function handleNext() {
    setSearching(true);
    const shortlistPath = generatePath(ROUTES.shortlist, { sessionId });
    try {
      const { count } = await searchSession(sessionId, answers);
      navigate(shortlistPath, { state: { count } });
    } catch (error) {
      showError(userMessage(error, SEARCH_ERROR));
      setSearching(false);
    }
  }

  if (searching) return <LoadingScreen message="Finding places..." />;

  return (
    <SetupStep question="How far are you willing to travel?" onNext={handleNext}>
      <OptionChips
        options={MODE_OPTIONS}
        selected={[answers.mode]}
        onToggle={(value) => update({ mode: value })}
      />
      <div>
        <p className="text-center text-3xl font-medium text-blue-950">{answers.minutes} min</p>
        <input
          type="range"
          min={MIN_MINUTES}
          max={MAX_MINUTES}
          step={MINUTES_STEP}
          value={answers.minutes}
          onChange={(e) => update({ minutes: Number(e.target.value) })}
          className="mt-4 w-full accent-blue-500"
        />
        <div className="mt-1 flex justify-between text-xs text-blue-300">
          <span>{MIN_MINUTES} min</span>
          <span>{MAX_MINUTES} min</span>
        </div>
      </div>
    </SetupStep>
  );
}
