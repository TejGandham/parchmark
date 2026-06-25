import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, resetAuthHooks, setAuthHooks } from "./http";
import {
  changePassword,
  exportNotes,
  getUserInfo,
  type UserInfoDTO,
} from "./settings";

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

describe("changePassword", () => {
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

  it("POSTs to /api/settings/change-password with the supplied passwords and bearer token", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { message: "Password changed" }));
    vi.stubGlobal("fetch", fetchMock);

    const payload = {
      current_password: "old pass typed",
      new_password: "new pass typed",
    };
    const result = await changePassword(payload);

    expect(calledUrl(fetchMock)).toContain("/api/settings/change-password");
    const init = calledInit(fetchMock);
    expect(init.method).toBe("POST");
    expect(authHeader(init)).toBe("Bearer access-token");
    expect(JSON.parse(String(init.body))).toEqual(payload);
    expect(result).toEqual({ message: "Password changed" });
  });

  it("rejects with ApiError carrying backend { detail } on password-change failure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(400, { detail: "Password change is not available" }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      changePassword({
        current_password: "wrong",
        new_password: "newSecurePassword123",
      }),
    ).rejects.toMatchObject({
      status: 400,
      detail: "Password change is not available",
    });
  });
});

describe("exportNotes", () => {
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

  it("GETs /api/settings/export-notes and returns the Blob plus backend filename", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("zip-data", {
        status: 200,
        headers: {
          "Content-Disposition":
            'attachment; filename="parchmark_notes_20260625_120000.zip"',
        },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await exportNotes();

    expect(calledUrl(fetchMock)).toContain("/api/settings/export-notes");
    const init = calledInit(fetchMock);
    expect(init.method).toBe("GET");
    expect(authHeader(init)).toBe("Bearer access-token");
    expect(await result.blob.text()).toBe("zip-data");
    expect(result.filename).toBe("parchmark_notes_20260625_120000.zip");
  });

  it("falls back to a default filename when Content-Disposition is absent", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(new Blob(["zip"]), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(exportNotes()).resolves.toMatchObject({
      filename: "parchmark_notes.zip",
    });
  });

  it("rejects with ApiError carrying backend { detail } on export failure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(500, { detail: "export failed" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(exportNotes()).rejects.toMatchObject({
      status: 500,
      detail: "export failed",
    });
  });
});
