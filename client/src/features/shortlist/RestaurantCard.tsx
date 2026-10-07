import type { Restaurant } from "../../api/sessions";
import { cuisineLabel, distanceLabel } from "./format";

/** One restaurant's user-facing details. Missing fields are simply left out. */
export default function RestaurantCard({ restaurant }: { restaurant: Restaurant }) {
  const subtitle = [
    restaurant.cuisine ? cuisineLabel(restaurant.cuisine) : null,
    restaurant.price_level ? "$".repeat(restaurant.price_level) : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <article className="flex h-full flex-col gap-3 rounded-3xl bg-white/80 p-6 shadow-sm">
      <h2 className="text-2xl font-medium text-blue-950">{restaurant.name}</h2>
      {subtitle && <p className="text-blue-500">{subtitle}</p>}
      {restaurant.rating !== null && (
        <p className="text-blue-900">
          <span className="text-amber-500">★</span> {restaurant.rating.toFixed(1)}
          {restaurant.rating_count !== null && (
            <span className="text-blue-400"> ({restaurant.rating_count.toLocaleString()} reviews)</span>
          )}
        </p>
      )}
      <p className="text-sm text-blue-900">{restaurant.address}</p>
      {restaurant.distance_m !== null && (
        <p className="text-sm text-blue-400">{distanceLabel(restaurant.distance_m)} away</p>
      )}
      {restaurant.maps_uri && (
        <a
          href={restaurant.maps_uri}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-auto text-sm font-medium text-blue-600 underline"
        >
          Open in Google Maps
        </a>
      )}
    </article>
  );
}
