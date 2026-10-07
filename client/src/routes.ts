/** Every URL pattern in one place. Build concrete paths with react-router's `generatePath`. */
export const ROUTES = {
  home: "/",
  search: "/search",
  setupAfter: "/session/:sessionId/setup/after",
  setupPrice: "/session/:sessionId/setup/price",
  setupDietary: "/session/:sessionId/setup/dietary",
  setupTravel: "/session/:sessionId/setup/travel",
  shortlist: "/session/:sessionId/shortlist",
} as const;
