import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ToastContext } from "./useToast";

const DISMISS_MS = 5000;

/** Renders the error toast at the top of the screen. One toast at a time; it auto-dismisses. */
export default function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const dismiss = useCallback(() => {
    clearTimeout(timer.current);
    setMessage(null);
  }, []);

  const showError = useCallback((next: string) => {
    clearTimeout(timer.current);
    setMessage(next);
    timer.current = setTimeout(() => setMessage(null), DISMISS_MS);
  }, []);

  useEffect(() => () => clearTimeout(timer.current), []);

  const api = useMemo(() => ({ showError }), [showError]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      {message && (
        <div className="pointer-events-none fixed inset-x-0 top-0 z-50 flex justify-center p-4">
          <div
            role="alert"
            className="card toast-in pointer-events-auto flex w-full max-w-md items-start gap-3 px-4 py-3 text-base text-ink shadow-lg ring-2 ring-danger"
          >
            <span
              aria-hidden="true"
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-danger text-sm font-bold text-surface"
            >
              !
            </span>
            <p className="flex-1">{message}</p>
            <button
              type="button"
              aria-label="Dismiss"
              className="text-muted hover:text-ink"
              onClick={dismiss}
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </ToastContext.Provider>
  );
}
