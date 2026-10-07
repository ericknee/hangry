import type { After, Dietary, SetupAnswers } from "../../types";

export const AFTER_OPTIONS: { value: After; label: string }[] = [
  { value: "breakfast", label: "Breakfast" },
  { value: "lunch", label: "Lunch" },
  { value: "dinner", label: "Dinner" },
  { value: "coffee_dessert", label: "Coffee & dessert" },
  { value: "drinks", label: "Drinks" },
];

export const PRICE_OPTIONS = [1, 2, 3, 4].map((level) => ({
  value: level,
  label: "$".repeat(level),
}));

export const DIETARY_OPTIONS: { value: Dietary; label: string }[] = [
  { value: "none", label: "None" },
  { value: "vegetarian", label: "Vegetarian" },
  { value: "vegan", label: "Vegan" },
  { value: "halal", label: "Halal" },
];

export const MIN_MINUTES = 5;
export const MAX_MINUTES = 60;
export const MINUTES_STEP = 5;

export const DEFAULT_ANSWERS: SetupAnswers = {
  after: null,
  priceLevels: [],
  dietary: "none",
  mode: "drive",
  minutes: 20,
};

const key = (sessionId: string) => `hangry.setup.${sessionId}`;

const isOneOf = <T extends string>(options: { value: T }[], v: unknown): v is T =>
  options.some((o) => o.value === v);

/**
 * Keeps each stored field that has a valid shape and falls back to the default for the rest.
 * Invalid fields are logged with console.warn but never thrown, so the flow keeps going.
 */
function sanitizeAnswers(stored: unknown): SetupAnswers {
  if (typeof stored !== "object" || stored === null || Array.isArray(stored)) {
    console.warn("Stored setup answers are not an object; using defaults.", stored);
    return DEFAULT_ANSWERS;
  }
  const s = stored as Record<string, unknown>;
  const answers: SetupAnswers = { ...DEFAULT_ANSWERS };
  const invalid = (field: string) =>
    console.warn(`Stored setup answer "${field}" is invalid; using the default.`, s[field]);

  if (s.after !== undefined) {
    if (s.after === null || isOneOf(AFTER_OPTIONS, s.after)) answers.after = s.after;
    else invalid("after");
  }
  if (s.priceLevels !== undefined) {
    const levels = s.priceLevels;
    const valid = PRICE_OPTIONS.map((o) => o.value);
    if (Array.isArray(levels) && levels.every((l) => valid.includes(l))) {
      answers.priceLevels = levels;
    } else invalid("priceLevels");
  }
  if (s.dietary !== undefined) {
    if (isOneOf(DIETARY_OPTIONS, s.dietary)) answers.dietary = s.dietary;
    else invalid("dietary");
  }
  if (s.mode !== undefined) {
    if (s.mode === "walk" || s.mode === "drive") answers.mode = s.mode;
    else invalid("mode");
  }
  if (s.minutes !== undefined) {
    const m = s.minutes;
    if (typeof m === "number" && Number.isFinite(m) && m >= MIN_MINUTES && m <= MAX_MINUTES) {
      answers.minutes = m;
    } else invalid("minutes");
  }
  return answers;
}

export function loadSetupAnswers(sessionId: string): SetupAnswers {
  try {
    const raw = sessionStorage.getItem(key(sessionId));
    return raw ? sanitizeAnswers(JSON.parse(raw)) : DEFAULT_ANSWERS;
  } catch (error) {
    console.warn("Could not read stored setup answers; using defaults.", error);
    return DEFAULT_ANSWERS;
  }
}

export function saveSetupAnswers(sessionId: string, answers: SetupAnswers): void {
  try {
    sessionStorage.setItem(key(sessionId), JSON.stringify(answers));
  } catch {
    // Storage can be unavailable (private mode); answers then live only in page state.
  }
}
