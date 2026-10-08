import { useEffect, useState, type ReactNode } from "react";
import { animate, motion, useMotionValue, useReducedMotion, useTransform } from "framer-motion";

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

type Exit = { id: string; dir: -1 | 1 };

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
  pulled: boolean; // the bottom card is sliding out from under the deck to land on top
  enterDelay: number | null; // set only for cards added after the first render
  onSwipe: (dir: -1 | 1) => void;
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

  // The top card flies out when a swipe or the Next button asks for it.
  useEffect(() => {
    if (!isTop || exitDir === null) return;
    const controls = animate(x, exitDir * FLY_OUT_PX, { duration: reduceMotion ? 0 : SLIDE_OUT_S, ease: "easeIn" });
    controls.then(onExited);
    return () => controls.stop();
  }, [isTop, exitDir, reduceMotion, x, onExited]);

  // The bottom card slides out to the side from under the deck (the reverse of the fly-out).
  useEffect(() => {
    if (!pulled) return;
    const controls = animate(x, -FLY_OUT_PX, { duration: reduceMotion ? 0 : SLIDE_OUT_S, ease: "easeOut" });
    controls.then(onPulled);
    return () => controls.stop();
  }, [pulled, reduceMotion, x, onPulled]);

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
          if (Math.abs(offset.x) > SWIPE_DISTANCE_PX || Math.abs(velocity.x) > SWIPE_VELOCITY) {
            onSwipe(offset.x < 0 ? -1 : 1);
            if (offset.x > 0) springBack(); // the card drops back one place as the bottom card comes up
            return;
          }
          // TODO(future): a downward swipe (offset.y > ~120) will interact with the restaurant (choose/save).
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
  children,
}: {
  label: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="flex h-14 w-14 items-center justify-center rounded-full bg-white text-blue-600 shadow-md hover:bg-blue-50"
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        {children}
      </svg>
    </button>
  );
}

/**
 * A deck of cards that cycles: swiping the top card sends it to the bottom, "previous" brings the
 * bottom card back. Cards added later slide in from the right and join the bottom of the deck.
 */
export default function CardDeck({
  items,
  onTopChange,
}: {
  items: DeckItem[];
  /** Called with the id of the top card on mount and whenever it changes. */
  onTopChange?: (id: string) => void;
}) {
  const [order, setOrder] = useState<string[]>(() => items.map((i) => i.id));
  const [exit, setExit] = useState<Exit | null>(null);
  const [pulledId, setPulledId] = useState<string | null>(null);
  const [initialIds] = useState(() => new Set(items.map((i) => i.id)));

  // Items added after mount join the end of the cycle; items that disappear are dropped.
  const ids = items.map((i) => i.id);
  const ordered = [...order.filter((id) => ids.includes(id)), ...ids.filter((id) => !order.includes(id))];
  const byId = new Map(items.map((i) => [i.id, i]));
  const newIds = ids.filter((id) => !initialIds.has(id));

  const topId = ordered[0];

  useEffect(() => {
    if (topId !== undefined) onTopChange?.(topId);
  }, [topId, onTopChange]);

  function requestExit(dir: -1 | 1) {
    if (exit || pulledId || ordered.length < 2) return;
    setExit({ id: topId, dir });
  }

  function finishExit() {
    setOrder([...ordered.slice(1), ordered[0]]);
    setExit(null);
  }

  function previous() {
    if (exit || pulledId || ordered.length < 2) return;
    setPulledId(ordered[ordered.length - 1]);
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
            pulled={pulledId === id}
            enterDelay={newIds.includes(id) ? newIds.indexOf(id) * ENTER_STAGGER_S : null}
            onSwipe={(dir) => (dir < 0 ? requestExit(-1) : previous())}
            onExited={finishExit}
            onPulled={finishPull}
          />
        ))}
      </div>
      <div className="mt-4 flex items-center gap-8">
        <RoundButton label="Previous restaurant" onClick={previous}>
          <path d="M15 5l-7 7 7 7" />
        </RoundButton>
        <span className="text-sm text-blue-700">
          {ids.indexOf(topId) + 1} / {items.length}
        </span>
        <RoundButton label="Next restaurant" onClick={() => requestExit(-1)}>
          <path d="M9 5l7 7-7 7" />
        </RoundButton>
      </div>
    </div>
  );
}
