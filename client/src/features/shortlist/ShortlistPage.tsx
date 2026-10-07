import { useEffect, useState, type ReactNode } from "react";
import { useLocation, useParams } from "react-router-dom";
import { getResults } from "../../api/sessions";
import CardDeck from "./CardDeck";
import LoadingScreen from "../../components/LoadingScreen";
import type { Restaurant } from "../../types";
import RestaurantCard from "./RestaurantCard";

const TOP_COUNT = 3;
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
  // The search step passes its own failure along, so there's nothing to fetch in that case.
  const searchError = (useLocation().state as { error?: string } | null)?.error ?? null;

  const [restaurants, setRestaurants] = useState<Restaurant[] | null>(null);
  const [error, setError] = useState<string | null>(searchError);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    if (searchError) return;
    let cancelled = false;
    getResults(sessionId)
      .then((results) => !cancelled && setRestaurants(results))
      .catch(() => !cancelled && setError(LOAD_ERROR));
    return () => {
      cancelled = true;
    };
  }, [sessionId, searchError]);

  if (error) {
    return (
      <Shell>
        <p className="text-center text-red-500">{error}</p>
      </Shell>
    );
  }
  if (restaurants === null) return <LoadingScreen message="Loading your shortlist..." />;
  if (restaurants.length === 0) {
    return (
      <Shell>
        <p className="text-center text-blue-900">No places found.</p>
      </Shell>
    );
  }

  const visible = showAll ? restaurants : restaurants.slice(0, TOP_COUNT);
  const hasMore = !showAll && restaurants.length > TOP_COUNT;

  return (
    <Shell>
      <h1 className="text-center text-2xl font-medium text-blue-950">Your shortlist</h1>
      <CardDeck cards={visible.map((r) => <RestaurantCard key={r.place_id} restaurant={r} />)} />
      {hasMore && (
        <button
          type="button"
          className="self-center rounded-full bg-white/80 px-5 py-3 text-sm font-medium text-blue-700 shadow-sm hover:bg-white"
          onClick={() => setShowAll(true)}
        >
          More recommendations
        </button>
      )}
    </Shell>
  );
}
