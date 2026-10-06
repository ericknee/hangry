import { useNavigate, useParams } from "react-router-dom";
import OptionChips from "../../components/OptionChips";
import SetupStep from "../../components/SetupStep";
import { PRICE_OPTIONS } from "../../lib/setupAnswers";
import { useSetupAnswers } from "../../lib/useSetupAnswers";

export default function PricePage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const [answers, update] = useSetupAnswers(sessionId);

  function toggle(level: number) {
    const next = answers.priceLevels.includes(level)
      ? answers.priceLevels.filter((l) => l !== level)
      : [...answers.priceLevels, level].sort();
    update({ priceLevels: next });
  }

  return (
    <SetupStep
      question="What's your price range?"
      onNext={() => navigate(`/session/${sessionId}/setup/dietary`)}
    >
      <OptionChips options={PRICE_OPTIONS} selected={answers.priceLevels} onToggle={toggle} />
    </SetupStep>
  );
}
