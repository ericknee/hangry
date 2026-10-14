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
            className={`min-h-[3rem] rounded-full border px-6 py-3 text-base font-medium shadow-sm transition-colors ${
              isSelected
                ? "border-accent bg-accent text-white"
                : "border-line bg-surface text-ink hover:border-accent"
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
