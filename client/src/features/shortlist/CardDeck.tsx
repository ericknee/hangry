import { useRef, useState, type ReactNode } from "react";

const SWIPE_THRESHOLD_PX = 50;

function Arrow({
  direction,
  disabled,
  onClick,
}: {
  direction: "left" | "right";
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={direction === "left" ? "Previous restaurant" : "Next restaurant"}
      disabled={disabled}
      onClick={onClick}
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/80 text-blue-600 shadow-sm transition-opacity hover:bg-white disabled:opacity-30"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d={direction === "left" ? "M15 5l-7 7 7 7" : "M9 5l7 7-7 7"} />
      </svg>
    </button>
  );
}

/** Shows one card at a time; arrows or a horizontal swipe move between them, stopping at the ends. */
export default function CardDeck({ cards }: { cards: ReactNode[] }) {
  const [index, setIndex] = useState(0);
  const touchStartX = useRef<number | null>(null);

  const prev = () => setIndex((i) => Math.max(0, i - 1));
  const next = () => setIndex((i) => Math.min(cards.length - 1, i + 1));

  function handleTouchEnd(e: React.TouchEvent) {
    if (touchStartX.current === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX.current;
    touchStartX.current = null;
    if (dx <= -SWIPE_THRESHOLD_PX) next();
    else if (dx >= SWIPE_THRESHOLD_PX) prev();
  }

  return (
    <div className="flex items-center gap-2">
      <Arrow direction="left" disabled={index === 0} onClick={prev} />
      <div
        className="min-w-0 flex-1 touch-pan-y"
        onTouchStart={(e) => {
          touchStartX.current = e.touches[0].clientX;
        }}
        onTouchEnd={handleTouchEnd}
      >
        {cards[index]}
      </div>
      <Arrow direction="right" disabled={index >= cards.length - 1} onClick={next} />
    </div>
  );
}
