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
