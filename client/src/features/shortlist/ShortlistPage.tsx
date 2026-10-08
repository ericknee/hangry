import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { userMessage } from "../../api/http";
import { getResults, photoUrl } from "../../api/sessions";
import CardDeck from "./CardDeck";
import LoadingScreen from "../../components/LoadingScreen";
import { useToast } from "../../components/useToast";
import type { Restaurant } from "../../types";
import { ROUTES } from "../../routes";
import RestaurantCard from "./RestaurantCard";

const TOP_COUNT = 3;
const PHOTO_BATCH = 5; // photos requested per batch; each one is a billed Places request
const PHOTO_LOOKAHEAD = 2; // start the next batch when a card this far ahead of the top has no photo yet
const LOAD_ERROR = "Couldn't load your results. Please try again.";

function Shell({ children }: { children: ReactNode }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 via-blue-100 to-blue-200 p-6">
      <div className="flex w-full max-w-md flex-col gap-4">{children}</div>
    </main>
  );
}

export default function ShortlistPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const { showError } = useToast();
  const [restaurants, setRestaurants] = useState<Restaurant[] | null>(null);
  const [showAll, setShowAll] = useState(false);
  // Ids whose photo may be requested. Cards outside it show the gradient and make no request.
  const [photoIds, setPhotoIds] = useState<Set<string>>(new Set());

  const visible = useMemo(
    () => (showAll ? (restaurants ?? []) : (restaurants ?? []).slice(0, TOP_COUNT)),
    [restaurants, showAll],
  );

  // Adds the next batch of cards (in rank order, from `from`) that don't have photos yet.
  const loadPhotoBatch = useCallback((list: Restaurant[], from: number) => {
    setPhotoIds((prev) => {
      const next = list
        .slice(from)
        .filter((r) => !prev.has(r.place_id))
        .slice(0, PHOTO_BATCH);
      return next.length === 0 ? prev : new Set([...prev, ...next.map((r) => r.place_id)]);
    });
  }, []);

  // As the user reaches cards without photos, load the next batch starting at the first of them.
  const onTopChange = useCallback(
    (topId: string) => {
      const top = visible.findIndex((r) => r.place_id === topId);
      if (top === -1) return;
      const missing = visible
        .slice(top, top + PHOTO_LOOKAHEAD + 1)
        .findIndex((r) => !photoIds.has(r.place_id));
      if (missing !== -1) loadPhotoBatch(visible, top + missing);
    },
    [visible, photoIds, loadPhotoBatch],
  );

  useEffect(() => {
    let cancelled = false;
    getResults(sessionId)
      .then((results) => {
        if (cancelled) return;
        setRestaurants(results);
        loadPhotoBatch(results.slice(0, TOP_COUNT), 0); // the shortlist's own photos
      })
      .catch((error) => {
        if (cancelled) return;
        showError(userMessage(error, LOAD_ERROR));
        navigate(ROUTES.home, { replace: true });
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId, showError, navigate, loadPhotoBatch]);

  if (restaurants === null) return <LoadingScreen message="Loading your shortlist..." />;
  if (restaurants.length === 0) {
    return (
      <Shell>
        <p className="text-center text-blue-900">No places found.</p>
      </Shell>
    );
  }

  const hasMore = !showAll && restaurants.length > TOP_COUNT;

  return (
    <Shell>
      <h1 className="text-center text-2xl font-medium text-blue-950">Your shortlist</h1>
      <CardDeck
        onTopChange={onTopChange}
        items={visible.map((r) => ({ id: r.place_id, content: (
            <RestaurantCard
              restaurant={r}
              photoUrl={r.photo && photoIds.has(r.place_id) ? photoUrl(sessionId, r.place_id) : null}
            />
          ),
        }))}
      />
      {hasMore && (
        <button
          type="button"
          className="self-center rounded-full bg-white/80 px-5 py-3 text-sm font-medium text-blue-700 shadow-sm hover:bg-white"
          onClick={() => {
            setShowAll(true);
            loadPhotoBatch(restaurants, TOP_COUNT);
          }}
        >
          More recommendations
        </button>
      )}
    </Shell>
  );
}
