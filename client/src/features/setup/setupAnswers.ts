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

export function loadSetupAnswers(sessionId: string): SetupAnswers {
  try {
    const raw = sessionStorage.getItem(key(sessionId));
    return raw ? { ...DEFAULT_ANSWERS, ...JSON.parse(raw) } : DEFAULT_ANSWERS;
  } catch {
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
