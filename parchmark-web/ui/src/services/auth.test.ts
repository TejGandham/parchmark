import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getCurrentUser, login, logout, refreshToken } from "./auth";
import { setAuthHooks } from "./http";

/** Build a `fetch`-compatible `Response` carrying a JSON body. */
function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function calledUrl(fetchMock: ReturnType<typeof vi.fn>, index = 0): string {
  const arg = fetchMock.mock.calls[index][0];
  return typeof arg === "string" ? arg : (arg as Request).url;
}

function calledInit(
  fetchMock: ReturnType<typeof vi.fn>,
  index = 0,
): RequestInit {
  return (fetchMock.mock.calls[index][1] ?? {}) as RequestInit;
}

const TOKEN_PAIR = {
  access_token: "access-1",
  refresh_token: "refresh-1",
  token_type: "bearer",
};

describe("auth service", () => {
  beforeEach(() => {
    setAuthHooks({
      getToken: () => "access-token",
      onRefresh: vi.fn().mockResolvedValue(true),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("login POSTs JSON credentials to /api/auth/login and returns the token pair", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, TOKEN_PAIR));
    vi.stubGlobal("fetch", fetchMock);

    const result = await login("qauser", "QaPass123!");

    expect(result).toEqual(TOKEN_PAIR);
    expect(calledUrl(fetchMock)).toContain("/api/auth/login");
    const init = calledInit(fetchMock);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      username: "qauser",
      password: "QaPass123!",
    });
  });

  it("login surfaces an ApiError with the backend detail on bad credentials", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(401, { detail: "Invalid username or password" }),
      );
    vi.stubGlobal("fetch", fetchMock);
    // No refresh recovery for login: onRefresh resolves false.
    setAuthHooks({
      getToken: () => null,
      onRefresh: vi.fn().mockResolvedValue(false),
    });

    await expect(login("qauser", "wrong")).rejects.toMatchObject({
      status: 401,
      detail: "Invalid username or password",
    });
  });

  it("refreshToken POSTs the refresh token and returns the new pair", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, TOKEN_PAIR));
    vi.stubGlobal("fetch", fetchMock);

    const result = await refreshToken("refresh-0");

    expect(result).toEqual(TOKEN_PAIR);
    expect(calledUrl(fetchMock)).toContain("/api/auth/refresh");
    expect(JSON.parse(calledInit(fetchMock).body as string)).toEqual({
      refresh_token: "refresh-0",
    });
  });

  it("getCurrentUser GETs /api/auth/me with the bearer header", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { username: "qauser" }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await getCurrentUser();

    expect(result).toEqual({ username: "qauser" });
    expect(calledUrl(fetchMock)).toContain("/api/auth/me");
    const init = calledInit(fetchMock);
    expect(init.method).toBe("GET");
    expect(
      new Headers(init.headers as HeadersInit | undefined).get("Authorization"),
    ).toBe("Bearer access-token");
  });

  it("logout POSTs to /api/auth/logout", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { message: "ok" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(logout()).resolves.toBeUndefined();
    expect(calledUrl(fetchMock)).toContain("/api/auth/logout");
    expect(calledInit(fetchMock).method).toBe("POST");
  });

  it("logout swallows errors (best effort)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(500, { detail: "boom" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(logout()).resolves.toBeUndefined();
  });
});
