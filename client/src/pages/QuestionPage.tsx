import TapOptionQuestion from "../components/TapOptionQuestion";

interface QuestionPageProps {
  question: string;
  options: string[];
  onSelect: (option: string) => void;
  /** Optional small caption above the question, e.g. "Round 2 of 4". */
  caption?: string;
}

/**
 * Reusable full-page layout for a single elicitation question. Rendered once
 * per round with a new question/options pair.
 */
export default function QuestionPage({
  question,
  options,
  onSelect,
  caption,
}: QuestionPageProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 via-blue-100 to-blue-200 p-6">
      <div className="flex w-full max-w-md flex-col gap-4">
        {caption && <p className="text-sm text-blue-400">{caption}</p>}
        <TapOptionQuestion question={question} options={options} onSelect={onSelect} />
      </div>
    </main>
  );
}
