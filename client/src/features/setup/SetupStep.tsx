import type { ReactNode } from "react";

interface SetupStepProps {
  question: string;
  children: ReactNode;
  onNext: () => void;
  nextDisabled?: boolean;
}

/** Full-page layout for one setup question: heading, answer controls, Next button. */
export default function SetupStep({ question, children, onNext, nextDisabled }: SetupStepProps) {
  return (
    <main className="page">
      <div className="flex w-full max-w-md flex-col gap-6">
        <h1 className="text-3xl font-bold tracking-tight text-ink">{question}</h1>
        {children}
        <button
          type="button"
          disabled={nextDisabled}
          className="btn-primary mt-2"
          onClick={onNext}
        >
          Next
        </button>
      </div>
    </main>
  );
}
