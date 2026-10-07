import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../../routes";
import { autocompleteCities, getCityLocation, type CityPrediction } from "../../api/places";
import { savePendingLocation, type PendingLocation } from "./pendingLocation";

const CURRENT_LOCATION_LABEL = "Current location";
const LOCATION_ERROR = "Couldn't get your location. Search for a city instead.";

function PinIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 21s-7-6.1-7-11a7 7 0 0 1 14 0c0 4.9-7 11-7 11Z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}

function CrosshairIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="7" />
      <circle cx="12" cy="12" r="2" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </svg>
  );
}

function getBrowserPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation unsupported"));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10_000 });
  });
}

export default function LocationPage() {
  const navigate = useNavigate();
  const [locationText, setLocationText] = useState("");
  const [selectedLocation, setSelectedLocation] = useState<PendingLocation | null>(null);
  const [predictions, setPredictions] = useState<CityPrediction[]>([]);
  const [showPredictions, setShowPredictions] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const requestId = useRef(0);

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
    setLocationError(null);
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

  async function selectCurrentLocation() {
    setPredictions([]);
    setShowPredictions(false);
    try {
      const { coords } = await getBrowserPosition();
      setLocationError(null);
      setLocationText(CURRENT_LOCATION_LABEL);
      setSelectedLocation({ lat: coords.latitude, lng: coords.longitude });
    } catch {
      setLocationError(LOCATION_ERROR);
    }
  }

  function handleNext() {
    savePendingLocation(selectedLocation);
    navigate(ROUTES.search);
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 via-blue-100 to-blue-200 p-6">
      <div className="flex w-full max-w-md flex-col gap-4">
        <h1 className="text-center text-4xl font-medium text-blue-950">Hangry?</h1>

        <div className="relative">
          <div className="flex items-center gap-3 rounded-2xl bg-white/80 p-3 shadow-sm">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-500">
              <PinIcon />
            </span>
            <input
              className="w-full bg-transparent text-blue-900 placeholder:text-blue-300 focus:outline-none"
              placeholder="Enter your location..."
              value={locationText}
              onChange={(e) => {
                setLocationText(e.target.value);
                setSelectedLocation(null);
                setLocationError(null);
              }}
              onFocus={() => setShowPredictions(true)}
              onBlur={() => setTimeout(() => setShowPredictions(false), 150)}
            />
          </div>
          {showPredictions && (
            <ul className="absolute inset-x-0 top-full z-10 mt-1 overflow-hidden rounded-2xl bg-white shadow-md">
              <li>
                <button
                  type="button"
                  className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm font-medium text-blue-600 hover:bg-blue-50"
                  onMouseDown={selectCurrentLocation}
                >
                  <CrosshairIcon />
                  {CURRENT_LOCATION_LABEL}
                </button>
              </li>
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
          {locationError && <p className="mt-2 px-2 text-sm text-red-500">{locationError}</p>}
        </div>

        <button
          type="button"
          className="mt-2 w-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400 py-4 font-medium text-white shadow-md transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:from-gray-300 disabled:to-gray-300 disabled:opacity-100 disabled:shadow-none"
          disabled={selectedLocation === null}
          onClick={handleNext}
        >
          Next
        </button>
      </div>
    </main>
  );
}
