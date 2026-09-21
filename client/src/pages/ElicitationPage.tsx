import { useParams } from "react-router-dom";
import TapOptionQuestion from "../components/TapOptionQuestion";

export default function ElicitationPage() {
  const { sessionId } = useParams();

  // TODO Phase 2: fetch the next generated question over WebSocket/REST
  // for this session instead of this placeholder.
  const placeholderQuestion = {
    question: "How far are you willing to travel?",
    options: ["5 min", "15 min", "30 min", "Doesn't matter"],
  };

  return (
    <main className="mx-auto flex max-w-md flex-col gap-4 p-8">
      <p className="text-sm text-gray-500">Session {sessionId}</p>
      <TapOptionQuestion
        question={placeholderQuestion.question}
        options={placeholderQuestion.options}
        onSelect={(option) => console.log("selected", option)}
      />
    </main>
  );
}
