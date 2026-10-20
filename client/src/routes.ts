/** Every URL pattern in one place. Build concrete paths with react-router's `generatePath`. */
export const ROUTES = {
  home: "/",
  terms: "/terms",
  privacy: "/privacy",
  search: "/search",
  setupAfter: "/session/:sessionId/setup/after",
  setupPrice: "/session/:sessionId/setup/price",
  setupDietary: "/session/:sessionId/setup/dietary",
  setupTravel: "/session/:sessionId/setup/travel",
  shortlist: "/session/:sessionId/shortlist",
  // Group sessions: the invite link, and one page that shows lobby, voting, waiting or result.
  join: "/join/:sessionId",
  group: "/session/:sessionId/group",
} as const;
