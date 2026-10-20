import { useEffect, useState } from "react";
import { submitVotes } from "../../api/groups";
import { ApiError, userMessage } from "../../api/http";
import { getResults, photoUrl } from "../../api/sessions";
import Button from "../../components/Button";
import LoadingScreen from "../../components/LoadingScreen";
import Page from "../../components/Page";
import { useToast } from "../../components/useToast";
import type { Restaurant, VoteValue } from "../../types";
import CardDeck from "../shortlist/CardDeck";
import RestaurantCard from "../shortlist/RestaurantCard";
import { usePhotoBatches } from "../shortlist/usePhotoBatches";
import { loadVoteDraft, saveVoteDraft } from "./groupStorage";
import type { GroupScreenProps } from "./screenProps";
import SessionOver from "./SessionOver";

const NO_RESTAURANTS: Restaurant[] = [];
const LOAD_ERROR = "Couldn't load the places. Please try again.";
const SUBMIT_ERROR = "Couldn't submit your votes. Please try again.";

/**
 * Everyone votes on the same places. The deck browses as usual (swipe sideways); a vote is a swipe
 * down (like) or up (dislike), or the two buttons. Votes are kept on this device until the one
 * submit, which needs every place voted on.
 */
export default function VoteScreen({ sessionId, participantId, apply, refresh }: GroupScreenProps) {
  const { showError } = useToast();
  const [restaurants, setRestaurants] = useState<Restaurant[] | null>(null);
  const [expired, setExpired] = useState(false);
  const [votes, setVotes] = useState<Record<string, VoteValue>>(() => loadVoteDraft(sessionId));
  const [submitting, setSubmitting] = useState(false);
  const { photoIds, loadPhotoBatch, onTopChange } = usePhotoBatches(restaurants ?? NO_RESTAURANTS);

  useEffect(() => {
    let cancelled = false;
    getResults(sessionId)
      .then((results) => {
        if (cancelled) return;
        setRestaurants(results);
        loadPhotoBatch(results, 0);
      })
      .catch((error) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 404) setExpired(true);
        else showError(userMessage(error, LOAD_ERROR));
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId, showError, loadPhotoBatch]);

  if (expired) return <SessionOver message="This session expired. Start a new one." />;
  if (restaurants === null) return <LoadingScreen message="Loading the places..." />;

  const votedCount = restaurants.filter((r) => votes[r.place_id] !== undefined).length;
  const allVoted = votedCount === restaurants.length;

  function handleVote(placeId: string, value: VoteValue) {
    const next = { ...votes, [placeId]: value };
    setVotes(next);
    saveVoteDraft(sessionId, next);
  }

  async function handleSubmit() {
    if (!restaurants || !allVoted || submitting) return;
    setSubmitting(true);
    try {
      const deckVotes = Object.fromEntries(restaurants.map((r) => [r.place_id, votes[r.place_id]]));
      apply(await submitVotes(sessionId, participantId, deckVotes));
      saveVoteDraft(sessionId, {});
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) setExpired(true);
      else if (error instanceof ApiError && error.status === 409) await refresh(); // already submitted, or over
      else showError(userMessage(error, SUBMIT_ERROR));
      setSubmitting(false);
    }
  }

  return (
    <Page>
      <h1 className="title text-center">Vote on each place</h1>
      <p className="text-center text-sm text-muted">
        Swipe down or tap the check to like, swipe up or tap the cross to dislike. Swipe sideways to
        browse.
      </p>
      <CardDeck
        onTopChange={onTopChange}
        onVote={handleVote}
        votes={votes}
        items={restaurants.map((r) => ({
          id: r.place_id,
          content: (
            <RestaurantCard
              restaurant={r}
              vote={votes[r.place_id] ?? null}
              photoUrl={r.photo && photoIds.has(r.place_id) ? photoUrl(sessionId, r.place_id) : null}
            />
          ),
        }))}
      />
      <p className="text-center text-sm font-medium text-muted">
        {votedCount} of {restaurants.length} voted
      </p>
      <Button aria-busy={submitting} disabled={!allVoted || submitting} onClick={handleSubmit}>
        Submit votes
      </Button>
    </Page>
  );
}
