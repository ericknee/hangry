interface TapOptionQuestionProps {
  question: string;
  options: string[];
  onSelect: (option: string) => void;
}

/**
 * Core elicitation UI per the project's UX decision: one question per
 * screen, large tap targets, no free text. Reused as-is in group mode —
 * same component, shown to each member in parallel.
 */
export default function TapOptionQuestion({
  question,
  options,
  onSelect,
}: TapOptionQuestionProps) {
  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-medium text-blue-950">{question}</h2>
      <div className="flex flex-wrap gap-3">
        {options.map((option) => (
          <button
            key={option}
            className="rounded-full bg-white/80 px-5 py-3 text-base text-blue-900 shadow-sm hover:bg-white active:bg-blue-50"
            onClick={() => onSelect(option)}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}
