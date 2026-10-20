import { useEffect, useRef, useState, type ReactNode } from "react";
import { animate, motion, useMotionValue, useReducedMotion, useTransform } from "framer-motion";
import Button from "../../components/Button";
import type { VoteValue } from "../../types";

export type DeckItem = { id: string; content: ReactNode };

const VISIBLE_SLOTS = 3; // top card plus two peeking behind it
const PEEK_OFFSET_PX = 14;
const PEEK_SCALE_STEP = 0.05;
const SWIPE_DISTANCE_PX = 80;
const SWIPE_VELOCITY = 1000;
const FLY_OUT_PX = 420;
const SLIDE_OUT_S = 0.2; // shared by the fly-out (Next) and the pull-out (Previous) so both feel the same
const ENTER_FROM_PX = 500;
const ENTER_STAGGER_S = 0.03;
const SPRING = { type: "spring", stiffness: 450, damping: 25 } as const; // Damping - higher value means less wiggle

// A card leaves sideways when browsing (x) and vertically when voted on (y: up = dislike, down = like).
type Exit = { id: string; dir: -1 | 1; axis: "x" | "y" };

function slotStyle(slot: number) {
  const depth = Math.min(slot, VISIBLE_SLOTS - 1);
  return {
    x: 0,
    y: depth * PEEK_OFFSET_PX,
    scale: 1 - depth * PEEK_SCALE_STEP,
    opacity: slot < VISIBLE_SLOTS ? 1 : 0,
  };
}

function DeckCard({
  item,
  slot,
  count,
  exitDir,
  exitAxis,
  voteEnabled,
  pulled,
  enterDelay,
  onSwipe,
  onExited,
  onPulled,
}: {
  item: DeckItem;
  slot: number;
  count: number;
  exitDir: -1 | 1 | null;
  exitAxis: "x" | "y";
  voteEnabled: boolean; // vertical swipes vote; without it they do nothing
  pulled: boolean; // the bottom card is sliding out from under the deck to land on top
  enterDelay: number | null; // set only for cards added after the first render
  onSwipe: (dir: -1 | 1, axis: "x" | "y") => boolean; // true if the deck started a move
  onExited: () => void;
  onPulled: () => void;
}) {
  const reduceMotion = useReducedMotion();
  const isTop = slot === 0;
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-15, 15]);
  const [settled, setSettled] = useState(enterDelay === null);

  // A card that was flown off (or dragged) and is now further back glides home underneath the stack.
  // A card pulled out from the bottom lands on top from where it was left.
  useEffect(() => {
    if (slot === 0) {
      if (x.get() !== 0) animate(x, 0, SPRING);
      return;
    }
    animate(x, 0, SPRING);
    animate(y, 0, SPRING);
  }, [slot, x, y]);

  // The callbacks are new closures every render; refs keep a re-render from restarting the animations.
  const onExitedRef = useRef(onExited);
  const onPulledRef = useRef(onPulled);
  useEffect(() => {
    onExitedRef.current = onExited;
    onPulledRef.current = onPulled;
  });

  // The top card flies out when a swipe or the Next button asks for it.
  useEffect(() => {
    if (!isTop || exitDir === null) return;
    const controls = animate(exitAxis === "y" ? y : x, exitDir * FLY_OUT_PX, {
      duration: reduceMotion ? 0 : SLIDE_OUT_S,
      ease: "easeIn",
    });
    controls.then(() => onExitedRef.current());
    return () => controls.stop();
  }, [isTop, exitDir, exitAxis, reduceMotion, x, y]);

  // The bottom card slides out to the side from under the deck (the reverse of the fly-out).
  useEffect(() => {
    if (!pulled) return;
    const controls = animate(x, -FLY_OUT_PX, { duration: reduceMotion ? 0 : SLIDE_OUT_S, ease: "easeOut" });
    controls.then(() => onPulledRef.current());
    return () => controls.stop();
  }, [pulled, reduceMotion, x]);

  function springBack() {
    animate(x, 0, SPRING);
    animate(y, 0, SPRING);
  }

  return (
    <motion.div
      className="absolute inset-0"
      style={{ zIndex: count - slot, pointerEvents: isTop ? "auto" : "none" }}
      initial={enterDelay === null ? false : { ...slotStyle(slot), x: ENTER_FROM_PX }}
      animate={pulled ? { ...slotStyle(slot), opacity: 1 } : slotStyle(slot)}
      transition={
        reduceMotion ? { duration: 0.15 } : { ...SPRING, delay: settled ? 0 : (enterDelay ?? 0) }
      }
      onAnimationComplete={() => setSettled(true)}
      aria-hidden={!isTop}
    >
      <motion.div
        className="h-full cursor-grab touch-none active:cursor-grabbing"
        style={{ x, y, rotate }}
        drag={isTop && exitDir === null}
        dragMomentum={false}
        dragElastic={0.8}
        onDragEnd={(_, info) => {
          const { offset, velocity } = info;
          const vertical = Math.abs(offset.y) > Math.abs(offset.x);
          if (
            voteEnabled &&
            vertical &&
            (Math.abs(offset.y) > SWIPE_DISTANCE_PX || Math.abs(velocity.y) > SWIPE_VELOCITY)
          ) {
            // Up (negative y) dislikes, down likes; a refused swipe (mid-animation) resets the card.
            if (!onSwipe(offset.y < 0 ? -1 : 1, "y")) springBack();
            return;
          }
          if (Math.abs(offset.x) > SWIPE_DISTANCE_PX || Math.abs(velocity.x) > SWIPE_VELOCITY) {
            const started = onSwipe(offset.x < 0 ? -1 : 1, "x");
            // Only a left swipe that started an exit leaves the card flying out. A right swipe
            // drops the card back one place as the bottom card comes up; a refused swipe resets it.
            if (!started || offset.x > 0) springBack();
            return;
          }
          springBack();
        }}
      >
        {item.content}
      </motion.div>
    </motion.div>
  );
}

function RoundButton({
  label,
  onClick,
  className,
  pressed,
  children,
}: {
  label: string;
  onClick: () => void;
  className?: string;
  pressed?: boolean;
  children: ReactNode;
}) {
  return (
    <Button
      variant="icon"
      aria-label={label}
      aria-pressed={pressed}
      className={className}
      onClick={onClick}
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        {children}
      </svg>
    </Button>
  );
}

/**
 * A deck of cards that cycles: swiping the top card sends it to the bottom, "previous" brings the
 * bottom card back. Cards added later slide in from the right and join the bottom of the deck.
 *
 * With `onVote` the deck also takes votes: swipe down (or press the check) to like the top card, up
 * (or the cross) to dislike it. A voted card leaves vertically and joins the bottom like any other,
 * and can be voted on again later. `votes` only marks which button reflects the top card's vote.
 */
export default function CardDeck({
  items,
  onTopChange,
  onVote,
  votes,
}: {
  items: DeckItem[];
  /** Called with the id of the top card on mount and whenever it changes. */
  onTopChange?: (id: string) => void;
  onVote?: (id: string, value: VoteValue) => void;
  votes?: Record<string, VoteValue>;
}) {
  const [order, setOrder] = useState<string[]>(() => items.map((i) => i.id));
  const [exit, setExit] = useState<Exit | null>(null);
  const [pulledId, setPulledId] = useState<string | null>(null);
  const [initialIds] = useState(() => new Set(items.map((i) => i.id)));

  // Items added after mount join the end of the cycle; items that disappear are dropped.
  const ids = items.map((i) => i.id);
  const idSet = new Set(ids);
  const orderSet = new Set(order);
  const ordered = [...order.filter((id) => idSet.has(id)), ...ids.filter((id) => !orderSet.has(id))];
  const byId = new Map(items.map((i) => [i.id, i]));
  const newIndex = new Map(ids.filter((id) => !initialIds.has(id)).map((id, i) => [id, i]));

  const topId = ordered[0];

  useEffect(() => {
    if (topId !== undefined) onTopChange?.(topId);
  }, [topId, onTopChange]);

  function requestExit(dir: -1 | 1): boolean {
    if (exit || pulledId || ordered.length < 2) return false;
    setExit({ id: topId, dir, axis: "x" });
    return true;
  }

  // The vote counts even in a one-card deck, which has nowhere to send the card.
  function requestVote(value: VoteValue): boolean {
    if (exit || pulledId || !onVote) return false;
    onVote(topId, value);
    if (ordered.length < 2) return false;
    setExit({ id: topId, dir: value, axis: "y" });
    return true;
  }

  function finishExit() {
    setOrder([...ordered.slice(1), ordered[0]]);
    setExit(null);
  }

  function previous(): boolean {
    if (exit || pulledId || ordered.length < 2) return false;
    setPulledId(ordered[ordered.length - 1]);
    return true;
  }

  function finishPull() {
    setOrder([ordered[ordered.length - 1], ...ordered.slice(0, -1)]);
    setPulledId(null);
  }

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="relative h-[30rem] w-full">
        {ordered.map((id, slot) => (
          <DeckCard
            key={id}
            item={byId.get(id)!}
            slot={slot}
            count={ordered.length}
            exitDir={exit?.id === id ? exit.dir : null}
            exitAxis={exit?.id === id ? exit.axis : "x"}
            voteEnabled={onVote !== undefined}
            pulled={pulledId === id}
            enterDelay={newIndex.has(id) ? newIndex.get(id)! * ENTER_STAGGER_S : null}
            onSwipe={(dir, axis) =>
              axis === "y" ? requestVote(dir) : dir < 0 ? requestExit(-1) : previous()
            }
            onExited={finishExit}
            onPulled={finishPull}
          />
        ))}
      </div>
      {onVote && (
        <div className="flex items-center gap-10">
          <RoundButton
            label="Dislike"
            pressed={votes?.[topId] === -1}
            className={votes?.[topId] === -1 ? "ring-2 ring-danger text-danger" : "text-danger"}
            onClick={() => requestVote(-1)}
          >
            <path d="M6 6l12 12M18 6L6 18" />
          </RoundButton>
          <RoundButton
            label="Like"
            pressed={votes?.[topId] === 1}
            className={
              votes?.[topId] === 1 ? "ring-2 ring-green-600 text-green-700" : "text-green-700"
            }
            onClick={() => requestVote(1)}
          >
            <path d="M5 13l4 4L19 7" />
          </RoundButton>
        </div>
      )}
      <div className="mt-4 flex items-center gap-8">
        <RoundButton label="Previous restaurant" onClick={previous}>
          <path d="M15 5l-7 7 7 7" />
        </RoundButton>
        <span className="text-sm font-medium text-muted">
          {ids.indexOf(topId) + 1} / {items.length}
        </span>
        <RoundButton label="Next restaurant" onClick={() => requestExit(-1)}>
          <path d="M9 5l7 7-7 7" />
        </RoundButton>
      </div>
    </div>
  );
}
