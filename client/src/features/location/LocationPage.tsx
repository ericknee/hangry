import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../../routes";
import { userMessage } from "../../api/http";
import Button from "../../components/Button";
import Page from "../../components/Page";
import TextInput from "../../components/TextInput";
import { useToast } from "../../components/useToast";
import { autocompleteCities, getCityLocation } from "../../api/places";
import type { CityPrediction, PendingLocation } from "../../types";
import { savePendingLocation } from "./pendingLocation";

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
  const { showError } = useToast();
  const [locationText, setLocationText] = useState("");
  const [selectedLocation, setSelectedLocation] = useState<PendingLocation | null>(null);
  const [predictions, setPredictions] = useState<CityPrediction[]>([]);
  const [showPredictions, setShowPredictions] = useState(false);
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
    let city;
    try {
      city = await getCityLocation(prediction.place_id);
    } catch (error) {
      showError(userMessage(error, "Couldn't load that location. Try another."));
      return;
    }
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
      setLocationText(CURRENT_LOCATION_LABEL);
      setSelectedLocation({ lat: coords.latitude, lng: coords.longitude });
    } catch (error) {
      console.error(error);
      showError(LOCATION_ERROR);
    }
  }

  function handleNext() {
    savePendingLocation(selectedLocation);
    navigate(ROUTES.search);
  }

  return (
    <Page>
      <h1 className="text-center text-5xl font-bold tracking-tight text-accent">Hangry?</h1>

      <div className="relative">
        <div className="card flex items-center gap-3 p-3 shadow-sm focus-within:border-accent">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent/10 text-accent">
            <PinIcon />
          </span>
          <TextInput
            variant="bare"
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
        {showPredictions && (
          <ul className="card absolute inset-x-0 top-full z-10 mt-1 overflow-hidden">
            <li>
              <button
                type="button"
                className="flex w-full items-center gap-2 px-4 py-3 text-left text-base font-semibold text-accent hover:bg-accent/10"
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
                  className="w-full px-4 py-3 text-left text-base text-ink hover:bg-accent/10"
                  onMouseDown={() => selectPrediction(prediction)}
                >
                  {prediction.description}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <Button className="mt-2" disabled={selectedLocation === null} onClick={handleNext}>
        Next
      </Button>
    </Page>
  );
}
