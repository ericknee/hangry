import { useNavigate, useParams } from "react-router-dom";
import OptionChips from "../../components/OptionChips";
import SetupStep from "../../components/SetupStep";
import { AFTER_OPTIONS } from "../../lib/setupAnswers";
import { useSetupAnswers } from "../../lib/useSetupAnswers";

export default function AfterPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const [answers, update] = useSetupAnswers(sessionId);

  return (
    <SetupStep
      question="What are you after?"
      nextDisabled={answers.after === null}
      onNext={() => navigate(`/session/${sessionId}/setup/price`)}
    >
      <OptionChips
        options={AFTER_OPTIONS}
        selected={answers.after ? [answers.after] : []}
        onToggle={(value) => update({ after: value })}
      />
    </SetupStep>
  );
}
