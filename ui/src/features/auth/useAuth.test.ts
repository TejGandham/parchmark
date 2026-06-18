import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AuthHooks } from "../../services/http";

// Mock the auth service so no real network calls happen. Each test re-imports
// `useAuth` after `vi.resetModules()` so the module-singleton state is isolated.
vi.mock("../../services/auth", () => ({
  login: vi.fn(),
  refreshToken: vi.fn(),
  getCurrentUser: vi.fn(),
  logout: vi.fn(),
}));

// Capture the hooks `useAuth` wires into the HTTP layer at module init, while
// keeping the rest of `http.ts` (notably `ApiError`) real.
let capturedHooks: AuthHooks | null = null;
vi.mock("../../services/http", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../services/http")>();
  return {
    ...actual,
    setAuthHooks: (hooks: AuthHooks) => {
      capturedHooks = hooks;
      actual.setAuthHooks(hooks);
    },
  };
});

const STORAGE_KEY = "pm_auth";

const TOKEN_PAIR = {
  access_token: "access-1",
  refresh_token: "refresh-1",
  token_type: "bearer",
};

/**
 * Re-import a fresh copy of the auth service mock, the auth store, and the
 * `ApiError` class. `vi.resetModules()` gives `useAuth` a fresh `http` module,
 * so tests must build `ApiError` instances from that same fresh module for the
 * store's `instanceof ApiError` check to hold.
 */
async function loadAuth() {
  const service = await import("../../services/auth");
  const { ApiError } = await import("../../services/http");
  const { useAuth } = await import("./useAuth");
  return { service, ApiError, auth: useAuth(), hooks: capturedHooks! };
}

/** Read and parse the persisted `pm_auth` session, or null when absent. */
function storedSession() {
  const raw = localStorage.getItem(STORAGE_KEY);
  return raw ? JSON.parse(raw) : null;
}

beforeEach(() => {
  localStorage.clear();
  capturedHooks = null;
  vi.resetModules();
  vi.clearAllMocks();
});

describe("useAuth", () => {
  it("login() persists tokens, fetches the user via /me, and authenticates", async () => {
    const { service, auth } = await loadAuth();
    vi.mocked(service.login).mockResolvedValue(TOKEN_PAIR);
    vi.mocked(service.getCurrentUser).mockResolvedValue({ username: "qauser" });

    const ok = await auth.login("qauser", "QaPass123!");

    expect(ok).toBe(true);
    expect(service.login).toHaveBeenCalledWith("qauser", "QaPass123!");
    expect(service.getCurrentUser).toHaveBeenCalledOnce();
    expect(auth.user.value).toEqual({ username: "qauser" });
    expect(auth.isAuthenticated.value).toBe(true);
    expect(auth.error.value).toBeNull();
    expect(auth.pending.value).toBe(false);

    const persisted = storedSession();
    expect(persisted.accessToken).toBe("access-1");
    expect(persisted.refreshToken).toBe("refresh-1");
    expect(persisted.user).toEqual({ username: "qauser" });
  });

  it("login() failure sets error from the backend detail and stays unauthenticated", async () => {
    const { service, ApiError, auth } = await loadAuth();
    vi.mocked(service.login).mockRejectedValue(
      new ApiError(401, "Invalid username or password"),
    );

    const ok = await auth.login("qauser", "wrong");

    expect(ok).toBe(false);
    expect(auth.error.value).toBe("Invalid username or password");
    expect(auth.isAuthenticated.value).toBe(false);
    expect(auth.user.value).toBeNull();
    expect(auth.pending.value).toBe(false);
    expect(storedSession()).toEqual({
      accessToken: null,
      refreshToken: null,
      user: null,
    });
  });

  it("login() failure with a non-ApiError uses a generic message", async () => {
    const { service, auth } = await loadAuth();
    vi.mocked(service.login).mockRejectedValue(new Error("network down"));

    const ok = await auth.login("qauser", "QaPass123!");

    expect(ok).toBe(false);
    expect(auth.error.value).toBe("Login failed.");
    expect(auth.isAuthenticated.value).toBe(false);
  });

  it("logout() clears the user, authentication, and the pm_auth entry", async () => {
    const { service, auth } = await loadAuth();
    vi.mocked(service.login).mockResolvedValue(TOKEN_PAIR);
    vi.mocked(service.getCurrentUser).mockResolvedValue({ username: "qauser" });
    vi.mocked(service.logout).mockResolvedValue(undefined);

    await auth.login("qauser", "QaPass123!");
    expect(auth.isAuthenticated.value).toBe(true);

    await auth.logout();

    expect(service.logout).toHaveBeenCalledOnce();
    expect(auth.user.value).toBeNull();
    expect(auth.isAuthenticated.value).toBe(false);
    expect(storedSession()).toEqual({
      accessToken: null,
      refreshToken: null,
      user: null,
    });
  });

  it("restoreSession() validates a stored token and sets the user via /me", async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: "access-1",
        refreshToken: "refresh-1",
        user: null,
      }),
    );
    const { service, auth } = await loadAuth();
    vi.mocked(service.getCurrentUser).mockResolvedValue({ username: "qauser" });

    await auth.restoreSession();

    expect(service.getCurrentUser).toHaveBeenCalledOnce();
    expect(auth.user.value).toEqual({ username: "qauser" });
    expect(auth.isAuthenticated.value).toBe(true);
  });

  it("restoreSession() clears the session when the stored token is rejected", async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: "stale",
        refreshToken: "refresh-1",
        user: { username: "qauser" },
      }),
    );
    const { service, ApiError, auth } = await loadAuth();
    vi.mocked(service.getCurrentUser).mockRejectedValue(
      new ApiError(401, "Not authenticated"),
    );

    await auth.restoreSession();

    expect(service.getCurrentUser).toHaveBeenCalledOnce();
    expect(auth.isAuthenticated.value).toBe(false);
    expect(auth.user.value).toBeNull();
    expect(storedSession()).toEqual({
      accessToken: null,
      refreshToken: null,
      user: null,
    });
  });

  it("restoreSession() is a no-op when no access token is stored", async () => {
    const { service, auth } = await loadAuth();

    await auth.restoreSession();

    expect(service.getCurrentUser).not.toHaveBeenCalled();
    expect(auth.isAuthenticated.value).toBe(false);
  });

  it("refresh() shares one in-flight request across concurrent callers", async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: "access-0",
        refreshToken: "refresh-0",
        user: { username: "qauser" },
      }),
    );
    const { service, auth } = await loadAuth();

    let resolveRefresh: (value: typeof TOKEN_PAIR) => void = () => {};
    vi.mocked(service.refreshToken).mockReturnValue(
      new Promise((resolve) => {
        resolveRefresh = resolve;
      }),
    );

    const calls = [auth.refresh(), auth.refresh(), auth.refresh()];
    resolveRefresh(TOKEN_PAIR);
    const results = await Promise.all(calls);

    expect(results).toEqual([true, true, true]);
    expect(service.refreshToken).toHaveBeenCalledOnce();
    expect(service.refreshToken).toHaveBeenCalledWith("refresh-0");
    expect(storedSession().accessToken).toBe("access-1");
  });

  it("refresh() clears the session and resolves false when no refresh token is stored", async () => {
    const { service, auth } = await loadAuth();

    const ok = await auth.refresh();

    expect(ok).toBe(false);
    expect(service.refreshToken).not.toHaveBeenCalled();
    expect(auth.isAuthenticated.value).toBe(false);
  });

  it("refresh() clears the session and resolves false on a failed refresh", async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: "access-0",
        refreshToken: "refresh-0",
        user: { username: "qauser" },
      }),
    );
    const { service, ApiError, auth } = await loadAuth();
    vi.mocked(service.refreshToken).mockRejectedValue(
      new ApiError(401, "Refresh token expired"),
    );

    const ok = await auth.refresh();

    expect(ok).toBe(false);
    expect(auth.isAuthenticated.value).toBe(false);
    expect(storedSession()).toEqual({
      accessToken: null,
      refreshToken: null,
      user: null,
    });
  });

  it("refresh() permits a fresh call after the shared promise settles", async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: "access-0",
        refreshToken: "refresh-0",
        user: { username: "qauser" },
      }),
    );
    const { service, auth } = await loadAuth();
    vi.mocked(service.refreshToken).mockResolvedValue(TOKEN_PAIR);

    await auth.refresh();
    await auth.refresh();

    expect(service.refreshToken).toHaveBeenCalledTimes(2);
  });

  it("wires HTTP hooks: getToken reads the stored token and onRefresh delegates to refresh()", async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: "access-0",
        refreshToken: "refresh-0",
        user: { username: "qauser" },
      }),
    );
    const { service, hooks } = await loadAuth();
    vi.mocked(service.refreshToken).mockResolvedValue(TOKEN_PAIR);

    expect(hooks.getToken()).toBe("access-0");

    const refreshed = await hooks.onRefresh();

    expect(refreshed).toBe(true);
    expect(service.refreshToken).toHaveBeenCalledWith("refresh-0");
    expect(hooks.getToken()).toBe("access-1");
  });
});
