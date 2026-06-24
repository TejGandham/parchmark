import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, resetAuthHooks, setAuthHooks } from "./http";
import { getUserInfo, type UserInfoDTO } from "./settings";

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

function authHeader(init: RequestInit): string | null {
  return new Headers(init.headers as HeadersInit | undefined).get(
    "Authorization",
  );
}

const accountInfo: UserInfoDTO = {
  username: "ada",
  email: "ada@example.com",
  created_at: "2024-01-15T10:30:00.000Z",
  notes_count: 7,
  auth_provider: "local",
};

describe("getUserInfo", () => {
  beforeEach(() => {
    setAuthHooks({
      getToken: () => "access-token",
      onRefresh: vi.fn().mockResolvedValue(true),
    });
  });

  afterEach(() => {
    resetAuthHooks();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("issues GET to /api/settings/user-info with the bearer token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, accountInfo));
    vi.stubGlobal("fetch", fetchMock);

    await getUserInfo();

    expect(calledUrl(fetchMock)).toContain("/api/settings/user-info");
    const init = calledInit(fetchMock);
    expect(init.method).toBe("GET");
    expect(authHeader(init)).toBe("Bearer access-token");
  });

  it("resolves to the UserInfoResponse body unchanged", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, accountInfo));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getUserInfo()).resolves.toEqual(accountInfo);
  });

  it("rejects with ApiError carrying backend { detail } on non-2xx", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(500, { detail: "settings failed" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getUserInfo()).rejects.toMatchObject({
      status: 500,
      detail: "settings failed",
    });
    await expect(getUserInfo()).rejects.toBeInstanceOf(ApiError);
  });
});
