import { ofetch, type FetchOptions, type IFetchError } from "ofetch";

/**
 * Typed error thrown by the HTTP layer for any non-2xx response (or a refresh
 * that could not recover a 401). Carries the HTTP {@link status} and a human
 * readable {@link detail}, read from the backend JSON body `{ detail }` and
 * falling back to the response status text.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/** Hooks injected by the auth store so this module never imports it (no cycle). */
export interface AuthHooks {
  /** Current access token, or `null` when unauthenticated. */
  getToken: () => string | null;
  /** Attempt a token refresh; resolve `true` on success, `false` otherwise. */
  onRefresh: () => Promise<boolean>;
}

let authHooks: AuthHooks | null = null;

/**
 * Wire the auth store into the HTTP layer. Called once during app start-up.
 * Kept as dependency injection so `http.ts` has no import of the auth store.
 */
export function setAuthHooks(hooks: AuthHooks): void {
  authHooks = hooks;
}

/** Clear any wired auth hooks (test/teardown helper). */
export function resetAuthHooks(): void {
  authHooks = null;
}

/** Resolve the API base URL, honoring `VITE_API_URL` and defaulting to `/api`. */
function resolveBaseURL(): string {
  return import.meta.env.VITE_API_URL ?? "/api";
}

/** Resolve an API path against the configured base URL for native fetch calls. */
function resolveRequestURL(path: string): string {
  const baseURL = resolveBaseURL().replace(/\/$/, "");
  const requestPath = path.replace(/^\//, "");
  return `${baseURL}/${requestPath}`;
}

// `retry: false` — this module owns the single refresh-and-retry policy, so
// ofetch must not also retry on its own (which would double-send and exhaust
// queued responses in tests / hit the server twice in production). The baseURL
// is resolved per request so the env override is read at call time.
const client = ofetch.create({ retry: false });

/** True when the request targets the refresh endpoint (must never be retried). */
function isRefreshCall(path: string): boolean {
  return path === "/auth/refresh" || path.endsWith("/auth/refresh");
}

/**
 * Turn an ofetch failure into an {@link ApiError}, reading `{ detail }` from the
 * backend JSON body and falling back to the response status text.
 */
function toApiError(error: IFetchError): ApiError {
  const status = error.status ?? 0;
  const data = error.data as { detail?: unknown } | undefined;
  const detail =
    typeof data?.detail === "string" && data.detail.length > 0
      ? data.detail
      : (error.statusText ?? error.message ?? "Request failed");
  return new ApiError(status, detail);
}

/** Convert a failed raw response into an {@link ApiError}. */
async function responseToApiError(response: Response): Promise<ApiError> {
  let detail = response.statusText || "Request failed";

  try {
    const data = (await response.clone().json()) as { detail?: unknown };
    if (typeof data.detail === "string" && data.detail.length > 0) {
      detail = data.detail;
    }
  } catch {
    // Non-JSON error bodies fall back to the response status text.
  }

  return new ApiError(response.status, detail);
}

/** Convert a native fetch transport failure into an {@link ApiError}. */
function transportToApiError(error: unknown): ApiError {
  return new ApiError(
    0,
    error instanceof Error ? error.message : String(error),
  );
}

/**
 * Perform a single request through the configured ofetch instance, attaching
 * the bearer token when present.
 */
function fetchOnce<T>(path: string, options: FetchOptions<"json">): Promise<T> {
  const token = authHooks?.getToken() ?? null;
  const headers = new Headers(options.headers as HeadersInit | undefined);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return client<T>(path, { ...options, baseURL: resolveBaseURL(), headers });
}

/** Perform one native fetch call, attaching the bearer token when present. */
function fetchRawOnce(path: string, options: RequestInit): Promise<Response> {
  const token = authHooks?.getToken() ?? null;
  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(resolveRequestURL(path), { ...options, headers });
}

/**
 * Typed request helper used by the auth API. Attaches the bearer token, and on
 * a 401 (for any call other than `/auth/refresh`) attempts a single refresh and
 * one retry before giving up. All non-2xx outcomes surface as {@link ApiError}.
 */
export async function request<T>(
  path: string,
  options: FetchOptions<"json"> = {},
): Promise<T> {
  try {
    return await fetchOnce<T>(path, options);
  } catch (error) {
    const fetchError = error as IFetchError;
    const canRetry =
      fetchError.status === 401 && !isRefreshCall(path) && authHooks !== null;

    if (!canRetry) {
      throw toApiError(fetchError);
    }

    const refreshed = await authHooks!.onRefresh();
    if (!refreshed) {
      throw toApiError(fetchError);
    }

    try {
      return await fetchOnce<T>(path, options);
    } catch (retryError) {
      throw toApiError(retryError as IFetchError);
    }
  }
}

/**
 * Open one authenticated raw request under the shared single refresh-and-retry
 * policy: attach the bearer token, and on a 401 (for any call other than
 * `/auth/refresh`) attempt exactly one refresh and one retry. Returns the
 * native Response so callers can read headers, a Blob body, or a streaming
 * `body`. All non-2xx outcomes surface as {@link ApiError}.
 */
async function openRawWithRetry(
  path: string,
  options: RequestInit,
): Promise<Response> {
  let response: Response;

  try {
    response = await fetchRawOnce(path, options);
  } catch (error) {
    throw transportToApiError(error);
  }

  if (response.ok) {
    return response;
  }

  const canRetry =
    response.status === 401 && !isRefreshCall(path) && authHooks !== null;

  if (!canRetry) {
    throw await responseToApiError(response);
  }

  const refreshed = await authHooks!.onRefresh();
  if (!refreshed) {
    throw await responseToApiError(response);
  }

  try {
    const retryResponse = await fetchRawOnce(path, options);
    if (retryResponse.ok) {
      return retryResponse;
    }
    throw await responseToApiError(retryResponse);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw transportToApiError(error);
  }
}

/**
 * Raw response helper for authenticated downloads. It preserves the same
 * single refresh-and-retry behavior as {@link request}, but returns the native
 * Response so callers can read headers and Blob bodies.
 */
export function requestRaw(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  return openRawWithRetry(path, options);
}

/**
 * Open an authenticated streaming request (e.g. Server-Sent Events) over the
 * same single refresh-and-retry policy as {@link requestRaw}. Defaults the
 * `Accept` header to `text/event-stream` and returns the open Response so the
 * caller can read `response.body` as a stream. A 401 raised before the stream
 * opens drives exactly one refresh-and-retry; pass an `AbortSignal` via
 * `options.signal` to tear the request down.
 */
export function requestStream(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(options.headers);
  if (!headers.has("Accept")) {
    headers.set("Accept", "text/event-stream");
  }
  return openRawWithRetry(path, { ...options, headers });
}
