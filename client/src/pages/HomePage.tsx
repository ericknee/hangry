import { useEffect, useRef, useState } from "react";
import { autocompleteCities, getCityLocation, type CityPrediction } from "../api/places";
import { createSession, type LocationInput } from "../api/sessions";

const KM_TO_MI = 0.621371;
const MIN_KM = 0.5;
const MAX_KM = 20;

function IconBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-500">
      {children}
    </span>
  );
}

function PinIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 21s-7-6.1-7-11a7 7 0 0 1 14 0c0 4.9-7 11-7 11Z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}

function DistanceIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

function CravingIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 22c4-3 7-6.5 7-11a7 7 0 1 0-14 0c0 4.5 3 8 7 11Z" />
      <path d="M12 8v3l2 1.5" />
    </svg>
  );
}

export default function HomePage() {
  const [locationText, setLocationText] = useState("");
  const [selectedLocation, setSelectedLocation] = useState<LocationInput | null>(null);
  const [predictions, setPredictions] = useState<CityPrediction[]>([]);
  const [showPredictions, setShowPredictions] = useState(false);
  const [unit, setUnit] = useState<"km" | "mi">("km");
  const [distanceKm, setDistanceKm] = useState(3);
  const [craving, setCraving] = useState("");
  const requestId = useRef(0);

  const displayDistance =
    unit === "km" ? distanceKm : Math.round(distanceKm * KM_TO_MI * 10) / 10;

  useEffect(() => {
    const id = ++requestId.current;
    const timer = setTimeout(async () => {
      if (selectedLocation || locationText.trim().length < 2) {
        if (requestId.current === id) setPredictions([]);
        return;
      }
      try {
        const results = await autocompleteCities(locationText);
        if (requestId.current === id) setPredictions(results);
      } catch {
        if (requestId.current === id) setPredictions([]);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [locationText, selectedLocation]);

  async function selectPrediction(prediction: CityPrediction) {
    setPredictions([]);
    setShowPredictions(false);
    const city = await getCityLocation(prediction.place_id);
    // Set together so the debounce effect sees a non-null selectedLocation in
    // the same render as the locationText change, and skips re-fetching.
    setLocationText(prediction.description);
    setSelectedLocation({
      place_id: city.place_id,
      lat: city.lat,
      lng: city.lng,
      formatted_address: city.formatted_address,
    });
  }

  async function handleNext() {
    const session = await createSession({
      mode: "solo",
      initialQuery: craving,
      location: selectedLocation,
      radiusKm: distanceKm,
    });
    window.location.href = `/session/${session.session_id}`;
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 via-blue-100 to-blue-200 p-6">
      <div className="flex w-full max-w-md flex-col gap-4">
        <h1 className="text-center text-4xl font-medium text-blue-950">Hangry?</h1>

        <div className="relative">
          <div className="flex items-center gap-3 rounded-2xl bg-white/80 p-3 shadow-sm">
            <IconBadge>
              <PinIcon />
            </IconBadge>
            <input
              className="w-full bg-transparent text-blue-900 placeholder:text-blue-300 focus:outline-none"
              placeholder="Enter your location..."
              value={locationText}
              onChange={(e) => {
                setLocationText(e.target.value);
                setSelectedLocation(null);
              }}
              onFocus={() => setShowPredictions(true)}
              onBlur={() => setTimeout(() => setShowPredictions(false), 150)}
            />
          </div>
          {showPredictions && predictions.length > 0 && (
            <ul className="absolute inset-x-0 top-full z-10 mt-1 overflow-hidden rounded-2xl bg-white shadow-md">
              {predictions.map((prediction) => (
                <li key={prediction.place_id}>
                  <button
                    type="button"
                    className="w-full px-4 py-2 text-left text-sm text-blue-900 hover:bg-blue-50"
                    onMouseDown={() => selectPrediction(prediction)}
                  >
                    {prediction.description}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-2xl bg-white/80 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <IconBadge>
                <DistanceIcon />
              </IconBadge>
              <span className="font-medium text-blue-950">Distance</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex rounded-full bg-blue-100 p-1 text-xs font-medium">
                <button
                  type="button"
                  className={`rounded-full px-3 py-1 transition-colors ${
                    unit === "km" ? "bg-blue-500 text-white" : "text-blue-400"
                  }`}
                  onClick={() => setUnit("km")}
                >
                  km
                </button>
                <button
                  type="button"
                  className={`rounded-full px-3 py-1 transition-colors ${
                    unit === "mi" ? "bg-blue-500 text-white" : "text-blue-400"
                  }`}
                  onClick={() => setUnit("mi")}
                >
                  mi
                </button>
              </div>
              <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-500">
                {displayDistance} {unit}
              </span>
            </div>
          </div>
          <input
            type="range"
            min={MIN_KM}
            max={MAX_KM}
            step={0.5}
            value={distanceKm}
            onChange={(e) => setDistanceKm(Number(e.target.value))}
            className="mt-4 w-full accent-blue-500"
          />
          <div className="mt-1 flex justify-between text-xs text-blue-300">
            <span>0.5 km</span>
            <span>10 km</span>
            <span>20 km</span>
          </div>
        </div>

        <div className="rounded-2xl bg-white/80 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <IconBadge>
              <CravingIcon />
            </IconBadge>
            <span className="font-medium text-blue-950">
              What are you craving? <span className="font-normal text-blue-300">optional</span>
            </span>
          </div>
          <input
            className="mt-3 w-full bg-transparent text-sm text-blue-900 placeholder:text-blue-300 focus:outline-none"
            placeholder="Sushi, something spicy, comfort food..."
            value={craving}
            onChange={(e) => setCraving(e.target.value)}
          />
        </div>

        <button
          type="button"
          className="mt-2 w-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400 py-4 font-medium text-white shadow-md transition-opacity hover:opacity-90"
          onClick={handleNext}
        >
          Next
        </button>
      </div>
    </main>
  );
}
