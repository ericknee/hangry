/** Retries after the first attempt, so a request is tried at most MAX_RETRIES + 1 times. */
const MAX_RETRIES = 3;
const BASE_DELAY_MS = 500;

export class ApiError extends Error {
  /** HTTP status, or null when the request never got a response (network failure). */
  status: number | null;

  constructor(message: string, status: number | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
}

// Network failures, rate limiting and server errors are worth retrying; other
// 4xx responses are the caller's fault and would fail identically again.
function isRetryable(error: ApiError): boolean {
  return error.status === null || error.status === 429 || error.status >= 500;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function attempt<T>(path: string, { method = "GET", body }: RequestOptions): Promise<T> {
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
  if (!res.ok) throw new ApiError(`Request failed: ${res.status}`, res.status);
  return res.json();
}

/**
 * Single entry point for backend calls. Retries retryable failures up to
 * MAX_RETRIES times with exponential backoff (500 ms, 1 s, 2 s) and always
 * rejects with an ApiError.
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  for (let retry = 0; ; retry++) {
    try {
      return await attempt<T>(path, options);
    } catch (error) {
      const apiError =
        error instanceof ApiError ? error : new ApiError("Unexpected error", null);
      if (retry >= MAX_RETRIES || !isRetryable(apiError)) throw apiError;
      await sleep(BASE_DELAY_MS * 2 ** retry);
    }
  }
}
