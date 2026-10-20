import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { userMessage } from "../../api/http";
import { getResults, photoUrl } from "../../api/sessions";
import CardDeck from "./CardDeck";
import Button from "../../components/Button";
import LoadingScreen from "../../components/LoadingScreen";
import Page from "../../components/Page";
import { useToast } from "../../components/useToast";
import type { Restaurant } from "../../types";
import { ROUTES } from "../../routes";
import RestaurantCard from "./RestaurantCard";
import { usePhotoBatches } from "./usePhotoBatches";

const TOP_COUNT = 3;
const LOAD_ERROR = "Couldn't load your results. Please try again.";

export default function ShortlistPage() {
  const { sessionId = "" } = useParams();
  const navigate = useNavigate();
  const { showError } = useToast();
  const [restaurants, setRestaurants] = useState<Restaurant[] | null>(null);
  const [showAll, setShowAll] = useState(false);

  const visible = useMemo(
    () => (showAll ? (restaurants ?? []) : (restaurants ?? []).slice(0, TOP_COUNT)),
    [restaurants, showAll],
  );
  const { photoIds, loadPhotoBatch, onTopChange } = usePhotoBatches(visible);

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
      <Page>
        <p className="text-center text-ink">No places found.</p>
      </Page>
    );
  }

  const hasMore = !showAll && restaurants.length > TOP_COUNT;

  return (
    <Page>
      <h1 className="title text-center">Your shortlist</h1>
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
        <Button
          variant="secondary"
          className="self-center"
          onClick={() => {
            setShowAll(true);
            loadPhotoBatch(restaurants, TOP_COUNT);
          }}
        >
          More recommendations
        </Button>
      )}
    </Page>
  );
}
