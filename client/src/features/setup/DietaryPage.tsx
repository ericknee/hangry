import { generatePath, useNavigate, useParams } from "react-router-dom";
import OptionChips from "../../components/OptionChips";
import SetupStep from "./SetupStep";
import { DIETARY_OPTIONS } from "./setupAnswers";
import { ROUTES } from "../../routes";
import { useSetupAnswers } from "./useSetupAnswers";

export default function DietaryPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const [answers, update] = useSetupAnswers(sessionId);

  return (
    <SetupStep
      question="Any dietary restrictions?"
      onNext={() => navigate(generatePath(ROUTES.setupTravel, { sessionId }))}
    >
      <OptionChips
        options={DIETARY_OPTIONS}
        selected={[answers.dietary]}
        onToggle={(value) => update({ dietary: value })}
      />
    </SetupStep>
  );
}
