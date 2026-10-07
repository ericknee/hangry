/** Retries after the first attempt, so a request is tried at most MAX_RETRIES + 1 times. */
const MAX_RETRIES = 3;
const BASE_DELAY_MS = 500;

export class ApiError extends Error {
  /** HTTP status, or null when the request never got a response (network failure). */
  status: number | null;
  /** The backend's `detail` text, for logs and debugging. Not written for end users. */
  detail: string | null;

  constructor(message: string, status: number | null, detail: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Text to show the user for a failed call: a connection hint when the server was unreachable,
 * otherwise the caller's own message. Backend details stay out of the UI; they go to the console.
 */
export function userMessage(error: unknown, fallback: string): string {
  console.error(error);
  if (error instanceof ApiError && error.status === null) {
    return "Can't reach the server. Check your connection and try again.";
  }
  return fallback;
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  /** Defaults to true for GET and false for POST; see `apiRequest`. */
  retry?: boolean;
}

// Network failures, rate limiting and server errors are worth retrying; other
// 4xx responses are the caller's fault and would fail identically again.
function isRetryable(error: ApiError): boolean {
  return error.status === null || error.status === 429 || error.status >= 500;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function attempt<T>(
  path: string,
  { method = "GET", body }: Pick<RequestOptions, "method" | "body">,
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Network error", null);
  }
  if (!res.ok) {
    let detail: string | null = null;
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") detail = data.detail;
    } catch {
      // Body wasn't JSON; the status alone has to do.
    }
    throw new ApiError(`Request failed: ${res.status}`, res.status, detail);
  }
  return res.json();
}

/**
 * Single entry point for backend calls. Retries retryable failures up to
 * MAX_RETRIES times with exponential backoff (500 ms, 1 s, 2 s) and always
 * rejects with an ApiError.
 *
 * Only GETs retry by default. A POST can have side effects (a billed Places
 * search, a new session row), and a failed response doesn't prove the server
 * did nothing, so replaying it could do the work twice. Pass `retry: true` only
 * for a POST that is safe to repeat.
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, retry: retryEnabled = method === "GET" } = options;
  for (let retry = 0; ; retry++) {
    try {
      return await attempt<T>(path, { method, body });
    } catch (error) {
      const apiError =
        error instanceof ApiError ? error : new ApiError("Unexpected error", null);
      if (!retryEnabled || retry >= MAX_RETRIES || !isRetryable(apiError)) throw apiError;
      await sleep(BASE_DELAY_MS * 2 ** retry);
    }
  }
}
