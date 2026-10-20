/** Retries after the first attempt, so a request is tried at most MAX_RETRIES + 1 times. */
const MAX_RETRIES = 3;
const BASE_DELAY_MS = 500;

interface ApiErrorInfo {
  /** The backend's `detail` text, for logs and debugging. Not written for end users. */
  detail?: string | null;
  /** Seconds from the `Retry-After` header (sent with 429). */
  retryAfterSeconds?: number | null;
  method: string;
  path: string;
}

export class ApiError extends Error {
  /** HTTP status, or null when the request never got a response (network failure). */
  status: number | null;
  detail: string | null;
  /** Seconds from the `Retry-After` header (sent with 429), or null if absent. */
  retryAfterSeconds: number | null;
  method: string;
  path: string;

  /** `reason` is a short cause, e.g. "HTTP 429" or "network error"; the message adds the request and detail. */
  constructor(reason: string, status: number | null, info: ApiErrorInfo) {
    const detail = info.detail ?? null;
    super(`${info.method} ${info.path} failed: ${reason}${detail ? ` (${detail})` : ""}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.retryAfterSeconds = info.retryAfterSeconds ?? null;
    this.method = info.method;
    this.path = info.path;
  }
}

/** The per-session limit can lock a user out for up to 30 minutes, so say how long, not "a moment". */
function waitHint(seconds: number | null): string {
  if (seconds === null || seconds <= 60) return "Wait a moment and try again.";
  return `Try again in about ${Math.ceil(seconds / 60)} minutes.`;
}

/**
 * Text to show the user for a failed call: a connection hint when the server was unreachable,
 * a slow-down hint when rate limited, otherwise the caller's own message. Backend details stay out of the UI; they go to the console.
 */
export function userMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    console.error(error.message, {
      status: error.status,
      detail: error.detail,
      retryAfterSeconds: error.retryAfterSeconds,
    });
  } else {
    console.error(error);
  }
  if (error instanceof ApiError && error.status === null) {
    return "Can't reach the server. Check your connection and try again.";
  }
  if (error instanceof ApiError && error.status === 429) {
    return `You're going a bit fast. ${waitHint(error.retryAfterSeconds)}`;
  }
  return fallback;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  /** Extra request headers, e.g. the group member's credential. */
  headers?: Record<string, string>;
  /** Defaults to true for GET and false for POST; see `apiRequest`. */
  retry?: boolean;
}

// Network failures and server errors are worth retrying. A 429 is not: the server has dropped
// the call and `Retry-After` says when it will accept another, so the user retries by hand after
// that. Other 4xx responses are the caller's fault and would fail identically again.
function isRetryable(error: ApiError): boolean {
  return error.status === null || error.status >= 500;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function attempt<T>(
  path: string,
  { method = "GET", body, headers }: Pick<RequestOptions, "method" | "body" | "headers">,
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method,
      headers:
        body === undefined && !headers
          ? undefined
          : { ...(body === undefined ? {} : { "Content-Type": "application/json" }), ...headers },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("network error", null, { method, path });
  }
  if (!res.ok) {
    let detail: string | null = null;
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") detail = data.detail;
    } catch {
      // Body wasn't JSON; the status alone has to do.
    }
    // Guard the missing header first: Number(null) is 0, which would read as "retry now".
    const header = res.headers.get("Retry-After");
    const retryAfter = header === null ? NaN : Number(header);
    throw new ApiError(`HTTP ${res.status}`, res.status, {
      detail,
      retryAfterSeconds: Number.isFinite(retryAfter) ? retryAfter : null,
      method,
      path,
    });
  }
  try {
    return await res.json();
  } catch {
    // A 200 whose body isn't JSON (e.g. a proxy's error page) would otherwise escape as a bare SyntaxError.
    throw new ApiError("response was not valid JSON", res.status, { method, path });
  }
}

/**
 * Single entry point for backend calls. Retries network failures and 5xx responses up to
 * MAX_RETRIES times with exponential backoff (500 ms, 1 s, 2 s) and always rejects with an
 * ApiError. A 429 is never retried automatically; the user retries by hand.
 *
 * Only GETs retry by default. A POST can have side effects (a billed Places
 * search, a new session row), and a failed response doesn't prove the server
 * did nothing, so replaying it could do the work twice. Pass `retry: true` only
 * for a POST that is safe to repeat.
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, headers, retry: retryEnabled = method === "GET" } = options;
  for (let retry = 0; ; retry++) {
    try {
      return await attempt<T>(path, { method, body, headers });
    } catch (error) {
      const apiError =
        error instanceof ApiError
          ? error
          : new ApiError("unexpected error", null, { method, path });
      if (!retryEnabled || retry >= MAX_RETRIES || !isRetryable(apiError)) throw apiError;
      await sleep(BASE_DELAY_MS * 2 ** retry);
    }
  }
}
