import { useCallback, useState } from "react";
import type { Restaurant } from "../../types";

const PHOTO_BATCH = 5; // photos requested per batch; each one is a billed Places request
const PHOTO_LOOKAHEAD = 2; // start the next batch when a card this far ahead of the top has no photo yet

/**
 * Which cards may request their photo. Cards outside the set show the gradient and make no request,
 * so photos load in small batches as the user nears cards that lack one.
 * `visible` is the list the deck currently shows, in rank order.
 */
export function usePhotoBatches(visible: Restaurant[]) {
  const [photoIds, setPhotoIds] = useState<Set<string>>(new Set());

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

  return { photoIds, loadPhotoBatch, onTopChange };
}
