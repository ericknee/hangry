import { useState } from "react";
import { Link, generatePath } from "react-router-dom";
import { startGroupSession, updateMe } from "../../api/groups";
import { ApiError, userMessage } from "../../api/http";
import Button from "../../components/Button";
import LoadingScreen from "../../components/LoadingScreen";
import Page from "../../components/Page";
import TextInput from "../../components/TextInput";
import { useToast } from "../../components/useToast";
import { ROUTES } from "../../routes";
import { loadSetupAnswers } from "../setup/setupAnswers";
import MemberList from "./MemberList";
import type { GroupScreenProps } from "./screenProps";

const MAX_NAME_LENGTH = 30; // matches the backend limit on display names
const MAX_CRAVING_LENGTH = 100; // matches the backend limit on cravings
const START_ERROR = "Couldn't search for restaurants. Please try again.";

/** Waiting room: the invite link, who has joined, and your own name and craving. The host starts. */
export default function LobbyScreen({ sessionId, participantId, status, refresh }: GroupScreenProps) {
  const { showError } = useToast();
  const { me, members } = status;
  const [name, setName] = useState(me.name);
  const [craving, setCraving] = useState(me.craving ?? "");
  const [saving, setSaving] = useState(false);
  const [starting, setStarting] = useState(false);
  const [copied, setCopied] = useState(false);

  const link = `${window.location.origin}${generatePath(ROUTES.join, { sessionId })}`;
  const dirty = name.trim() !== me.name || craving.trim() !== (me.craving ?? "");
  const setupAnswers = loadSetupAnswers(sessionId);
  const canShare = typeof navigator.share === "function";

  async function save(): Promise<boolean> {
    setSaving(true);
    try {
      const updated = await updateMe(sessionId, participantId, { name, craving });
      setName(updated.name);
      setCraving(updated.craving ?? "");
      await refresh();
      return true;
    } catch (error) {
      const started = error instanceof ApiError && error.status === 409;
      showError(started ? "The host already started." : userMessage(error, "Couldn't save that."));
      return false;
    } finally {
      setSaving(false);
    }
  }

  async function handleStart() {
    if (dirty && !(await save())) return;
    setStarting(true);
    try {
      const { count } = await startGroupSession(sessionId, participantId, setupAnswers);
      if (count === 0) showError("No places found. Try different answers or cravings.");
      await refresh();
    } catch (error) {
      const busy = error instanceof ApiError && error.status === 409;
      showError(busy ? "The search is already running." : userMessage(error, START_ERROR));
    } finally {
      setStarting(false);
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      showError("Couldn't copy the link. Select it and copy it by hand.");
    }
  }

  async function shareLink() {
    try {
      await navigator.share({ title: "Pick a restaurant with me", url: link });
    } catch {
      // Closing the share sheet rejects; nothing to do.
    }
  }

  if (starting) return <LoadingScreen message="Finding places for everyone..." />;

  return (
    <Page gap="gap-6">
      <h1 className="title-lg">{me.is_host ? "Invite your friends" : "Waiting for the host"}</h1>

      <div className="flex flex-col gap-2">
        <p className="break-all rounded-2xl border border-line bg-surface px-4 py-3 text-sm text-ink">
          {link}
        </p>
        <div className="flex gap-3">
          <Button variant="secondary" className="flex-1" onClick={copyLink}>
            {copied ? "Copied" : "Copy link"}
          </Button>
          {canShare && (
            <Button variant="secondary" className="flex-1" onClick={shareLink}>
              Share
            </Button>
          )}
        </div>
      </div>

      <section className="flex flex-col gap-2">
        <h2 className="font-semibold text-ink">Who&apos;s in ({members.length}/8)</h2>
        <MemberList members={members} meName={me.name} />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-semibold text-ink">About you</h2>
        <TextInput
          aria-label="Your name"
          placeholder="Your name"
          maxLength={MAX_NAME_LENGTH}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <TextInput
          aria-label="What are you craving?"
          placeholder="What are you craving? (optional)"
          maxLength={MAX_CRAVING_LENGTH}
          value={craving}
          onChange={(e) => setCraving(e.target.value)}
        />
        {dirty && (
          <Button variant="secondary" aria-busy={saving} disabled={saving} onClick={() => void save()}>
            Save changes
          </Button>
        )}
      </section>

      {me.is_host ? (
        <>
          {setupAnswers.after === null && (
            <p className="text-center text-sm text-muted">
              Choose what you&apos;re after first.{" "}
              <Link to={generatePath(ROUTES.setupAfter, { sessionId })} className="underline">
                Answer the questions
              </Link>
            </p>
          )}
          <Button disabled={setupAnswers.after === null || saving} onClick={() => void handleStart()}>
            Start
          </Button>
        </>
      ) : (
        <p className="text-center text-muted">The host will start the search soon.</p>
      )}
    </Page>
  );
}
