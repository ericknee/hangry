import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getResults, photoUrl } from "../../api/sessions";
import Button from "../../components/Button";
import Page from "../../components/Page";
import { ROUTES } from "../../routes";
import type { PlaceTally } from "../../types";
import RestaurantCard from "../shortlist/RestaurantCard";
import type { GroupScreenProps } from "./screenProps";
import SessionOver from "./SessionOver";

const RUNNERS_UP = 2;

function names(list: string[]): string {
  return list.join(", ");
}

function RunnerUp({ tally, name }: { tally: PlaceTally; name: string }) {
  return (
    <li className="card flex flex-col gap-1 p-4">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-semibold text-ink">{name}</span>
        <span className="shrink-0 text-sm text-muted">
          {tally.likes} liked · {tally.dislikes} disliked
        </span>
      </div>
      {tally.liked_by.length > 0 && (
        <p className="text-sm text-ink">Liked by {names(tally.liked_by)}</p>
      )}
      {tally.disliked_by.length > 0 && (
        <p className="text-sm text-muted">Disliked by {names(tally.disliked_by)}</p>
      )}
    </li>
  );
}

/** The winner with who liked it, and the next places. */
export default function ResultScreen({ sessionId, status }: GroupScreenProps) {
  const navigate = useNavigate();
  // Names for the runners-up; the result only carries ids for them. Best effort: without them the
  // rows are left out.
  const [placeNames, setPlaceNames] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;
    getResults(sessionId)
      .then((list) => {
        if (!cancelled) setPlaceNames(Object.fromEntries(list.map((r) => [r.place_id, r.name])));
      })
      .catch((error) => console.warn("Could not load the place names", error));
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  const { result } = status;
  if (result === null) return <SessionOver message="This session expired." />;

  const winnerTally = result.tallies.find((t) => t.place_id === result.winner.place_id);
  const runnersUp = result.tallies
    .filter((t) => t.place_id !== result.winner.place_id && placeNames[t.place_id])
    .slice(0, RUNNERS_UP);

  return (
    <Page gap="gap-6">
      <h1 className="title-lg text-center">Your group&apos;s pick</h1>
      <RestaurantCard
        restaurant={result.winner}
        photoUrl={result.winner.photo ? photoUrl(sessionId, result.winner.place_id) : null}
      />
      <div className="text-center">
        {result.no_likes ? (
          <p className="font-semibold text-ink">No one picked, but this ranks best</p>
        ) : (
          winnerTally && (
            <>
              <p className="font-semibold text-ink">Liked by {names(winnerTally.liked_by)}</p>
              {winnerTally.disliked_by.length > 0 && (
                <p className="text-sm text-muted">Disliked by {names(winnerTally.disliked_by)}</p>
              )}
            </>
          )
        )}
      </div>
      {runnersUp.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="font-semibold text-ink">Also considered</h2>
          <ul className="flex flex-col gap-3">
            {runnersUp.map((tally) => (
              <RunnerUp key={tally.place_id} tally={tally} name={placeNames[tally.place_id]} />
            ))}
          </ul>
        </section>
      )}
      <Button variant="secondary" className="self-center" onClick={() => navigate(ROUTES.home)}>
        Start over
      </Button>
    </Page>
  );
}
