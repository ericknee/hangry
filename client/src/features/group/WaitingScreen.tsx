import { useState } from "react";
import { endGroupSession } from "../../api/groups";
import { userMessage } from "../../api/http";
import Button from "../../components/Button";
import Page from "../../components/Page";
import { useToast } from "../../components/useToast";
import MemberList from "./MemberList";
import type { GroupScreenProps } from "./screenProps";

/** After you submit: who has finished, and for the host a way to end voting for everyone. */
export default function WaitingScreen({ sessionId, participantId, status, apply }: GroupScreenProps) {
  const { showError } = useToast();
  const [confirming, setConfirming] = useState(false);
  const [ending, setEnding] = useState(false);

  async function handleEnd() {
    setEnding(true);
    try {
      apply(await endGroupSession(sessionId, participantId));
    } catch (error) {
      showError(userMessage(error, "Couldn't end voting. Please try again."));
      setEnding(false);
      setConfirming(false);
    }
  }

  return (
    <Page gap="gap-6">
      <h1 className="title-lg">Waiting for everyone</h1>
      <p className="text-muted">
        Your votes are in. The winner shows up as soon as everyone has finished.
      </p>
      <MemberList members={status.members} meName={status.me.name} showProgress />
      {status.me.is_host &&
        (confirming ? (
          <div className="flex flex-col gap-3">
            <p className="text-center text-sm text-muted">
              Anyone still swiping won&apos;t be counted.
            </p>
            <Button aria-busy={ending} disabled={ending} onClick={() => void handleEnd()}>
              End voting now
            </Button>
            <Button variant="secondary" disabled={ending} onClick={() => setConfirming(false)}>
              Keep waiting
            </Button>
          </div>
        ) : (
          <Button variant="secondary" onClick={() => setConfirming(true)}>
            End now
          </Button>
        ))}
    </Page>
  );
}
