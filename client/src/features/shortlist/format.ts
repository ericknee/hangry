/** "thai_restaurant" -> "Thai", "fast_food_restaurant" -> "Fast Food", "bar" -> "Bar". */
export function cuisineLabel(primaryType: string): string {
  return primaryType
    .replace(/_restaurant$/, "")
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** Straight-line distance from the search point, e.g. "450 m" or "3.2 km". */
export function distanceLabel(metres: number): string {
  if (metres < 1000) return `${Math.max(10, Math.round(metres / 10) * 10)} m`;
  return `${(metres / 1000).toFixed(1)} km`;
}
