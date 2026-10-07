interface OptionChipsProps<T extends string | number> {
  options: { value: T; label: string }[];
  selected: T[];
  onToggle: (value: T) => void;
}

/** Tap targets that show which options are selected; the parent decides single vs. multi-select. */
export default function OptionChips<T extends string | number>({
  options,
  selected,
  onToggle,
}: OptionChipsProps<T>) {
  return (
    <div className="flex flex-wrap gap-3">
      {options.map((option) => {
        const isSelected = selected.includes(option.value);
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isSelected}
            className={`rounded-full px-5 py-3 text-base shadow-sm transition-colors ${
              isSelected ? "bg-blue-500 text-white" : "bg-white/80 text-blue-900 hover:bg-white"
            }`}
            onClick={() => onToggle(option.value)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
