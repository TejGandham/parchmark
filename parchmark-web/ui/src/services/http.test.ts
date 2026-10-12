import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  request,
  requestRaw,
  requestStream,
  resetAuthHooks,
  setAuthHooks,
} from "./http";

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

describe("http requestRaw", () => {
  beforeEach(() => {
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

  it("returns the raw response with Authorization attached", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("zip-bytes", {
        status: 200,
        headers: { "Content-Type": "application/zip" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await requestRaw("/settings/export-notes", {
      method: "GET",
    });

    expect(response.headers.get("Content-Type")).toContain("application/zip");
    expect(await response.text()).toBe("zip-bytes");
    expect(calledUrl(fetchMock)).toContain("/api/settings/export-notes");
    expect(authHeader(calledInit(fetchMock))).toBe("Bearer access-token");
  });

  it("refreshes once and retries a raw request on 401", async () => {
    const onRefresh = vi.fn().mockResolvedValue(true);
    setAuthHooks({ getToken: () => "access-token", onRefresh });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(new Response("zip", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await requestRaw("/settings/export-notes", {
      method: "GET",
    });

    expect(await response.text()).toBe("zip");
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("throws ApiError details for raw non-2xx responses", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(500, { detail: "export failed" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      requestRaw("/settings/export-notes", { method: "GET" }),
    ).rejects.toMatchObject({
      status: 500,
      detail: "export failed",
    });
  });
});

describe("http requestStream", () => {
  /** Build a 200 Server-Sent Events response (an open, readable stream). */
  function streamResponse(): Response {
    return new Response("", {
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
    });
  }

  beforeEach(() => {
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

  it("opens the stream with Authorization and an event-stream Accept header", async () => {
    const fetchMock = vi.fn().mockResolvedValue(streamResponse());
    vi.stubGlobal("fetch", fetchMock);

    const response = await requestStream("/notes/events");

    expect(response.status).toBe(200);
    expect(calledUrl(fetchMock)).toContain("/api/notes/events");
    const init = calledInit(fetchMock);
    expect(authHeader(init)).toBe("Bearer access-token");
    expect(
      new Headers(init.headers as HeadersInit | undefined).get("Accept"),
    ).toBe("text/event-stream");
  });

  it("refreshes once and retries once when the stream open returns 401", async () => {
    const onRefresh = vi.fn().mockResolvedValue(true);
    setAuthHooks({ getToken: () => "access-token", onRefresh });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
      .mockResolvedValueOnce(streamResponse());
    vi.stubGlobal("fetch", fetchMock);

    const response = await requestStream("/notes/events");

    expect(response.status).toBe(200);
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("does not retry the stream open when the refresh fails", async () => {
    const onRefresh = vi.fn().mockResolvedValue(false);
    setAuthHooks({ getToken: () => "access-token", onRefresh });
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { detail: "nope" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestStream("/notes/events")).rejects.toMatchObject({
      status: 401,
    });
    expect(onRefresh).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("throws ApiError when the stream open fails with a non-401 status", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(500, { detail: "stream boom" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestStream("/notes/events")).rejects.toMatchObject({
      status: 500,
      detail: "stream boom",
    });
  });

  it("forwards an abort signal to the underlying fetch", async () => {
    const fetchMock = vi.fn().mockResolvedValue(streamResponse());
    vi.stubGlobal("fetch", fetchMock);
    const controller = new AbortController();

    await requestStream("/notes/events", { signal: controller.signal });

    expect(calledInit(fetchMock).signal).toBe(controller.signal);
  });
});
