import { useCallback, useEffect, useRef, useState } from "react";
import { getGroupStatus, groupEventsUrl } from "../../api/groups";
import { ApiError } from "../../api/http";
import type { GroupStatus } from "../../types";

const RECONNECT_DELAY_MS = 5000;

/**
 * The live status of a group session for one member.
 *
 * The server pushes a full snapshot on connect and after every change, so the stream and a plain
 * fetch are handled the same way. The fetch is also the fallback: it runs on mount and whenever the
 * tab becomes visible again, since phones suspend background connections. A browser reconnects a
 * dropped stream by itself, but not one the server refused, so that case is retried here.
 *
 * `apply` and `refresh` let the member's own actions update the screen at once instead of waiting
 * for the stream. `error` is set only when the server says this member or session does not exist
 * (403/404).
 */
export function useGroupStatus(sessionId: string, participantId: string) {
  const [status, setStatus] = useState<GroupStatus | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const source = useRef<EventSource | null>(null);
  const finished = useRef(false); // a finished session never changes again

  const refresh = useCallback(
    () =>
      getGroupStatus(sessionId, participantId)
        .then(setStatus)
        .catch((e: unknown) => {
          if (e instanceof ApiError && (e.status === 403 || e.status === 404)) setError(e);
          else console.warn("Could not refresh the group status", e);
        }),
    [sessionId, participantId],
  );

  useEffect(() => {
    let cancelled = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    finished.current = false;

    function connect() {
      if (cancelled || finished.current) return;
      const stream = new EventSource(groupEventsUrl(sessionId, participantId));
      source.current = stream;
      stream.addEventListener("status", (event) => {
        if (!cancelled) setStatus(JSON.parse((event as MessageEvent).data));
      });
      stream.onerror = () => {
        // CLOSED means the browser gave up (the server refused or answered with an error).
        if (stream.readyState === EventSource.CLOSED && !cancelled && !finished.current) {
          retryTimer = setTimeout(connect, RECONNECT_DELAY_MS);
        }
      };
    }

    function onVisible() {
      if (document.visibilityState === "visible" && !finished.current) void refresh();
    }

    void refresh();
    connect();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
      source.current?.close();
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [sessionId, participantId, refresh]);

  // Once the result is in, nothing more will be pushed: stop listening.
  const done = status?.phase === "done";
  useEffect(() => {
    if (done) {
      finished.current = true;
      source.current?.close();
    }
  }, [done]);

  return { status, error, apply: setStatus, refresh };
}
