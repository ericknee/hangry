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
    <div className="flex flex-col gap-3">
      <h2 className="text-lg font-medium">{question}</h2>
      <div className="grid grid-cols-2 gap-3">
        {options.map((option) => (
          <button
            key={option}
            className="rounded-lg border p-4 text-left text-base hover:bg-gray-50 active:bg-gray-100"
            onClick={() => onSelect(option)}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}
