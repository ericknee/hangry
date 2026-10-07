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
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 via-blue-100 to-blue-200 p-6">
      <div className="flex w-full max-w-md flex-col gap-6">
        <h1 className="text-2xl font-medium text-blue-950">{question}</h1>
        {children}
        <button
          type="button"
          disabled={nextDisabled}
          className="mt-2 w-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400 py-4 font-medium text-white shadow-md transition-opacity hover:opacity-90 disabled:opacity-50"
          onClick={onNext}
        >
          Next
        </button>
      </div>
    </main>
  );
}
