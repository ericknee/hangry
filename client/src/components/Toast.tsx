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
            className="toast-in pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700 shadow-lg ring-1 ring-red-200"
          >
            <p className="flex-1">{message}</p>
            <button
              type="button"
              aria-label="Dismiss"
              className="text-red-400 hover:text-red-600"
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
