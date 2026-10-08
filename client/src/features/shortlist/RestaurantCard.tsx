import { useState } from "react";
import type { Restaurant } from "../../types";
import { cuisineGradient, cuisineLabel, distanceLabel } from "./format";

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full bg-white/25 px-3 py-1 text-sm font-medium text-white backdrop-blur-sm">
      {children}
    </span>
  );
}

/** Google requires the photographer's credit wherever their photo is shown. */
function PhotoCredit({ name, uri }: { name: string; uri: string | null }) {
  const className = "absolute right-3 top-3 rounded bg-black/40 px-2 py-0.5 text-xs text-white/90";
  if (!uri) return <span className={className}>Photo: {name}</span>;
  return (
    <a href={uri} target="_blank" rel="noopener noreferrer" draggable={false} className={className}>
      Photo: {name}
    </a>
  );
}

/**
 * One restaurant's user-facing details. Missing fields are simply left out.
 * `photoUrl` is optional: without it (or if it fails to load) the hero shows a cuisine gradient.
 */
export default function RestaurantCard({
  restaurant,
  photoUrl,
}: {
  restaurant: Restaurant;
  photoUrl?: string | null;
}) {
  const [photoFailed, setPhotoFailed] = useState(false);
  const showPhoto = Boolean(photoUrl) && !photoFailed;
  const cuisine = restaurant.cuisine ? cuisineLabel(restaurant.cuisine) : null;
  const price = restaurant.price_level ? "$".repeat(restaurant.price_level) : null;

  return (
    <article className="flex h-[30rem] select-none flex-col overflow-hidden rounded-3xl bg-white shadow-lg">
      <div
        className="relative flex flex-[3] flex-col justify-end gap-3 p-5"
        style={{ background: cuisineGradient(restaurant.cuisine) }}
      >
        {showPhoto && (
          <img
            src={photoUrl!}
            alt=""
            draggable={false}
            onError={() => setPhotoFailed(true)}
            className="absolute inset-0 h-full w-full object-cover"
          />
        )}
        {showPhoto && restaurant.photo?.author_name && (
          <PhotoCredit name={restaurant.photo.author_name} uri={restaurant.photo.author_uri} />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
        <div className="relative flex flex-col gap-3">
          <h2 className="text-3xl font-semibold leading-tight text-white drop-shadow">{restaurant.name}</h2>
          <div className="flex flex-wrap gap-2">
            {restaurant.rating !== null && (
              <Pill>
                ★ {restaurant.rating.toFixed(1)}
                {restaurant.rating_count !== null && ` (${restaurant.rating_count.toLocaleString()})`}
              </Pill>
            )}
            {cuisine && <Pill>{cuisine}</Pill>}
            {price && <Pill>{price}</Pill>}
            {restaurant.distance_m !== null && <Pill>{distanceLabel(restaurant.distance_m)}</Pill>}
          </div>
        </div>
      </div>
      <div className="flex flex-[1] flex-col justify-between gap-2 p-5">
        <p className="text-sm text-blue-900">{restaurant.address}</p>
        {restaurant.maps_uri && (
          <a
            href={restaurant.maps_uri}
            target="_blank"
            rel="noopener noreferrer"
            draggable={false}
            className="self-start text-sm font-medium text-blue-600 underline"
          >
            Open in Google Maps
          </a>
        )}
      </div>
    </article>
  );
}
