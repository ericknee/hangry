import { useNavigate, useParams } from "react-router-dom";
import OptionChips from "../../components/OptionChips";
import SetupStep from "../../components/SetupStep";
import { DIETARY_OPTIONS } from "../../lib/setupAnswers";
import { useSetupAnswers } from "../../lib/useSetupAnswers";

export default function DietaryPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const [answers, update] = useSetupAnswers(sessionId);

  return (
    <SetupStep
      question="Any dietary restrictions?"
      onNext={() => navigate(`/session/${sessionId}/setup/travel`)}
    >
      <OptionChips
        options={DIETARY_OPTIONS}
        selected={[answers.dietary]}
        onToggle={(value) => update({ dietary: value })}
      />
    </SetupStep>
  );
}
