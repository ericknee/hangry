import { generatePath, useNavigate, useParams } from "react-router-dom";
import OptionChips from "../../components/OptionChips";
import SetupStep from "./SetupStep";
import { AFTER_OPTIONS } from "./setupAnswers";
import { ROUTES } from "../../routes";
import { useSetupAnswers } from "./useSetupAnswers";

export default function AfterPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const [answers, update] = useSetupAnswers(sessionId);

  return (
    <SetupStep
      question="What are you after?"
      nextDisabled={answers.after === null}
      onNext={() => navigate(generatePath(ROUTES.setupPrice, { sessionId }))}
    >
      <OptionChips
        options={AFTER_OPTIONS}
        selected={answers.after ? [answers.after] : []}
        onToggle={(value) => update({ after: value })}
      />
    </SetupStep>
  );
}
