import { useStorage } from "@vueuse/core";
import { computed, type ComputedRef, ref } from "vue";

import {
  getCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
  refreshToken as refreshTokenRequest,
} from "../../services/auth";
import { ApiError, setAuthHooks } from "../../services/http";

/** The authenticated user, as reported by `GET /auth/me`. */
export interface AuthUser {
  username: string;
}

/** Shape of the session object persisted under the `pm_auth` storage key. */
interface AuthSession {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
}

/** localStorage key holding the entire persisted session as a single object. */
const STORAGE_KEY = "pm_auth";

const EMPTY_SESSION: AuthSession = {
  accessToken: null,
  refreshToken: null,
  user: null,
};

// Module-singleton reactive session, persisted to localStorage via @vueuse.
// `useStorage` keeps this in sync with the `pm_auth` entry across reloads and
// serialises the whole `{ accessToken, refreshToken, user }` object as JSON.
const session = useStorage<AuthSession>(STORAGE_KEY, { ...EMPTY_SESSION });

const user: ComputedRef<AuthUser | null> = computed(() => session.value.user);

const error = ref<string | null>(null);
const pending = ref(false);

const isAuthenticated: ComputedRef<boolean> = computed(
  () => Boolean(session.value.accessToken) && session.value.user !== null,
);

// Shared in-flight refresh, so N concurrent 401s trigger exactly one network
// call to `/auth/refresh`. Reset to null once the call settles.
let refreshPromise: Promise<boolean> | null = null;

/** Persist a fresh token pair into the reactive session. */
function setTokens(accessToken: string, refreshTokenValue: string): void {
  session.value = {
    ...session.value,
    accessToken,
    refreshToken: refreshTokenValue,
  };
}

/** Wipe the entire session, clearing the persisted `pm_auth` entry. */
function clearSession(): void {
  session.value = { ...EMPTY_SESSION };
}

/**
 * Exchange the stored refresh token for a new token pair. Concurrent callers
 * share a single in-flight request; the shared promise resets once it settles.
 */
function refresh(): Promise<boolean> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const storedRefresh = session.value.refreshToken;
    if (!storedRefresh) {
      clearSession();
      return false;
    }

    try {
      const pair = await refreshTokenRequest(storedRefresh);
      setTokens(pair.access_token, pair.refresh_token);
      return true;
    } catch {
      clearSession();
      return false;
    }
  })().finally(() => {
    refreshPromise = null;
  });

  return refreshPromise;
}

// Wire the HTTP layer to this store: the bearer token is read from the
// persisted session, and a 401 drives a single shared refresh-and-retry.
setAuthHooks({
  getToken: () => session.value.accessToken,
  onRefresh: () => refresh(),
});

/**
 * Authenticate with credentials. Stores the token pair, then fetches the
 * canonical user from `/auth/me` (the login response carries no user). Resolves
 * `true` on success; on failure sets {@link error} and clears any partial
 * session, resolving `false`.
 */
async function login(username: string, password: string): Promise<boolean> {
  pending.value = true;
  error.value = null;

  try {
    const pair = await loginRequest(username, password);
    setTokens(pair.access_token, pair.refresh_token);

    const me = await getCurrentUser();
    session.value = { ...session.value, user: { username: me.username } };
    return true;
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.detail : "Login failed.";
    clearSession();
    return false;
  } finally {
    pending.value = false;
  }
}

/** Best-effort server logout, then clear the local session unconditionally. */
async function logout(): Promise<void> {
  await logoutRequest();
  clearSession();
}

/**
 * Validate a stored access token on app start. A valid token refreshes the
 * cached user; a 401 (or any {@link ApiError}) clears the session. No-op when
 * no access token is stored.
 */
async function restoreSession(): Promise<void> {
  if (!session.value.accessToken) {
    return;
  }

  try {
    const me = await getCurrentUser();
    session.value = { ...session.value, user: { username: me.username } };
  } catch {
    clearSession();
  }
}

/**
 * Reactive auth store as a composable singleton. All consumers share one
 * persisted session; calling this multiple times returns the same refs.
 */
export function useAuth() {
  return {
    user,
    isAuthenticated,
    error,
    pending,
    login,
    logout,
    restoreSession,
    refresh,
  };
}
