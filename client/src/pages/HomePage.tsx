import { useState } from "react";
import { createSession } from "../api/sessions";

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
  const [location, setLocation] = useState("");
  const [unit, setUnit] = useState<"km" | "mi">("km");
  const [distanceKm, setDistanceKm] = useState(3);
  const [craving, setCraving] = useState("");

  const displayDistance =
    unit === "km" ? distanceKm : Math.round(distanceKm * KM_TO_MI * 10) / 10;

  async function handleNext() {
    const session = await createSession("solo", craving);
    window.location.href = `/session/${session.session_id}`;
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-50 via-blue-100 to-blue-200 p-6">
      <div className="flex w-full max-w-md flex-col gap-4">
        <h1 className="text-center text-4xl font-medium text-blue-950">Hangry?</h1>

        <div className="flex items-center gap-3 rounded-2xl bg-white/80 p-3 shadow-sm">
          <IconBadge>
            <PinIcon />
          </IconBadge>
          <input
            className="w-full bg-transparent text-blue-900 placeholder:text-blue-300 focus:outline-none"
            placeholder="Enter your location..."
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
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
