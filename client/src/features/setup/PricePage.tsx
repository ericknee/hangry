import { generatePath, useNavigate, useParams } from "react-router-dom";
import OptionChips from "../../components/OptionChips";
import SetupStep from "./SetupStep";
import { PRICE_OPTIONS } from "./setupAnswers";
import { ROUTES } from "../../routes";
import { useSetupAnswers } from "./useSetupAnswers";

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
      onNext={() => navigate(generatePath(ROUTES.setupDietary, { sessionId }))}
    >
      <OptionChips options={PRICE_OPTIONS} selected={answers.priceLevels} onToggle={toggle} />
    </SetupStep>
  );
}
