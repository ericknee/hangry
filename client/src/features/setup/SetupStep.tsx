import type { ReactNode } from "react";
import Button from "../../components/Button";
import Page from "../../components/Page";

interface SetupStepProps {
  question: string;
  children: ReactNode;
  onNext: () => void;
  nextDisabled?: boolean;
}

/** Full-page layout for one setup question: heading, answer controls, Next button. */
export default function SetupStep({ question, children, onNext, nextDisabled }: SetupStepProps) {
  return (
    <Page gap="gap-6">
      <h1 className="title-lg">{question}</h1>
      {children}
      <Button disabled={nextDisabled} className="mt-2" onClick={onNext}>
        Next
      </Button>
    </Page>
  );
}
