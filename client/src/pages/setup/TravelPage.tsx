import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { searchSession } from "../../api/sessions";
import LoadingScreen from "../../components/LoadingScreen";
import OptionChips from "../../components/OptionChips";
import SetupStep from "../../components/SetupStep";
import {
  MAX_MINUTES,
  MIN_MINUTES,
  MINUTES_STEP,
  type TravelMode,
} from "../../lib/setupAnswers";
import { useSetupAnswers } from "../../lib/useSetupAnswers";

const MODE_OPTIONS: { value: TravelMode; label: string }[] = [
  { value: "walk", label: "Walking" },
  { value: "drive", label: "Driving" },
];

const SEARCH_ERROR = "Couldn't search for restaurants. Please try again.";

export default function TravelPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const [answers, update] = useSetupAnswers(sessionId);
  const [searching, setSearching] = useState(false);

  async function handleNext() {
    setSearching(true);
    const shortlistPath = `/session/${sessionId}/shortlist`;
    try {
      const { count } = await searchSession(sessionId, answers);
      navigate(shortlistPath, { state: { count } });
    } catch {
      navigate(shortlistPath, { state: { error: SEARCH_ERROR } });
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
