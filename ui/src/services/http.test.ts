import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, request, resetAuthHooks, setAuthHooks } from "./http";

/** Build a `fetch`-compatible `Response` carrying a JSON body. */
function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Resolve the absolute URL ofetch passed to the stubbed fetch for a call. */
function calledUrl(fetchMock: ReturnType<typeof vi.fn>, index = 0): string {
  const arg = fetchMock.mock.calls[index][0];
  return typeof arg === "string" ? arg : (arg as Request).url;
}

/** Resolve the RequestInit ofetch passed to the stubbed fetch for a call. */
function calledInit(
  fetchMock: ReturnType<typeof vi.fn>,
  index = 0,
): RequestInit {
  return (fetchMock.mock.calls[index][1] ?? {}) as RequestInit;
}

/** Read the Authorization header from a stubbed fetch call's init. */
function authHeader(init: RequestInit): string | null {
  return new Headers(init.headers as HeadersInit | undefined).get(
    "Authorization",
  );
}

describe("http request", () => {
  beforeEach(() => {
    // Default: authenticated, refresh never needed.
    setAuthHooks({
      getToken: () => "access-token",
      onRefresh: vi.fn().mockResolvedValue(true),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it("attaches the bearer header when a token is present", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { username: "qauser" }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await request<{ username: string }>("/auth/me", {
      method: "GET",
    });

    expect(result).toEqual({ username: "qauser" });
    expect(calledUrl(fetchMock)).toContain("/api/auth/me");
    expect(authHeader(calledInit(fetchMock))).toBe("Bearer access-token");
  });

  it("omits the bearer header when getToken returns null", async () => {
    setAuthHooks({
      getToken: () => null,
      onRefresh: vi.fn().mockResolvedValue(true),
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await request("/auth/me", { method: "GET" });

    expect(authHeader(calledInit(fetchMock))).toBeNull();
  });

  it("refreshes once and retries once on a 401, returning the retried result", async () => {
    const onRefresh = vi.fn().mockResolvedValue(true);
    setAuthHooks({ getToken: () => "access-token", onRefresh });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(jsonResponse(200, { username: "qauser" }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await request<{ username: string }>("/auth/me", {
      method: "GET",
    });

    expect(result).toEqual({ username: "qauser" });
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("throws ApiError {401} when the refresh fails", async () => {
    const onRefresh = vi.fn().mockResolvedValue(false);
    setAuthHooks({ getToken: () => "access-token", onRefresh });

    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(401, { detail: "Invalid username or password" }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(request("/auth/me", { method: "GET" })).rejects.toMatchObject({
      status: 401,
      detail: "Invalid username or password",
    });
    expect(onRefresh).toHaveBeenCalledTimes(1);
    // original call + nothing retried (refresh failed) => exactly one fetch.
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("throws ApiError when the retried request also fails", async () => {
    const onRefresh = vi.fn().mockResolvedValue(true);
    setAuthHooks({ getToken: () => "access-token", onRefresh });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(jsonResponse(500, { detail: "boom" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(request("/auth/me", { method: "GET" })).rejects.toMatchObject({
      status: 500,
      detail: "boom",
    });
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("never refreshes or retries the /auth/refresh call itself", async () => {
    const onRefresh = vi.fn().mockResolvedValue(true);
    setAuthHooks({ getToken: () => "access-token", onRefresh });

    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { detail: "bad refresh" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      request("/auth/refresh", {
        method: "POST",
        body: { refresh_token: "x" },
      }),
    ).rejects.toMatchObject({ status: 401, detail: "bad refresh" });
    expect(onRefresh).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("throws ApiError carrying the backend detail and status on non-2xx", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(422, { detail: "Unprocessable" }));
    vi.stubGlobal("fetch", fetchMock);

    let error: ApiError | undefined;
    try {
      await request("/auth/login", {
        method: "POST",
        body: { username: "a", password: "b" },
      });
    } catch (e) {
      error = e as ApiError;
    }

    expect(error).toBeInstanceOf(ApiError);
    expect(error?.status).toBe(422);
    expect(error?.detail).toBe("Unprocessable");
    expect(error?.message).toBe("Unprocessable");
  });

  it("falls back to the status text when the body has no detail", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("nope", {
        status: 503,
        statusText: "Service Unavailable",
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    let error: ApiError | undefined;
    try {
      await request("/auth/login", {
        method: "POST",
        body: { username: "a", password: "b" },
      });
    } catch (e) {
      error = e as ApiError;
    }

    expect(error).toBeInstanceOf(ApiError);
    expect(error?.status).toBe(503);
    expect(error?.detail).toBe("Service Unavailable");
  });

  it("does not attempt a refresh when no auth hooks are registered", async () => {
    resetAuthHooks();
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { detail: "unauthorized" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(request("/auth/me", { method: "GET" })).rejects.toMatchObject({
      status: 401,
      detail: "unauthorized",
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("wraps a transport failure (no status) as an ApiError with status 0", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error("network down"));
    vi.stubGlobal("fetch", fetchMock);

    let error: ApiError | undefined;
    try {
      await request("/auth/me", { method: "GET" });
    } catch (e) {
      error = e as ApiError;
    }

    expect(error).toBeInstanceOf(ApiError);
    expect(error?.status).toBe(0);
    expect(error?.detail).toContain("network down");
  });

  it("honors the '/api' default base URL", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await request("/auth/me", { method: "GET" });

    expect(calledUrl(fetchMock)).toContain("/api/auth/me");
  });

  it("honors the VITE_API_URL override", async () => {
    vi.stubEnv("VITE_API_URL", "https://api.example.test");
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await request("/auth/me", { method: "GET" });

    expect(calledUrl(fetchMock)).toBe("https://api.example.test/auth/me");
    vi.unstubAllEnvs();
  });
});
