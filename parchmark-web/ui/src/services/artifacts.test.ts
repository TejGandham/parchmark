import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  createViewLink,
  deleteArtifact,
  getArtifactContent,
  listArtifacts,
  setArtifactVisibility,
  type ArtifactDTO,
} from "./artifacts";
import { ApiError, resetAuthHooks, setAuthHooks } from "./http";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function calledUrl(fetchMock: ReturnType<typeof vi.fn>): string {
  const arg = fetchMock.mock.calls[0][0];
  return typeof arg === "string" ? arg : (arg as Request).url;
}

function calledInit(fetchMock: ReturnType<typeof vi.fn>): RequestInit {
  return (fetchMock.mock.calls[0][1] ?? {}) as RequestInit;
}

function authHeader(init: RequestInit): string | null {
  return new Headers(init.headers as HeadersInit | undefined).get(
    "Authorization",
  );
}

const artifact: ArtifactDTO = {
  id: 7,
  slug: "s3cr3t-slug",
  title: "Quarterly chart",
  visibility: "private",
  created_at: "2026-10-01T10:00:00Z",
  current_version: {
    id: 11,
    version: 2,
    content_type: "html",
    created_at: "2026-10-02T10:00:00Z",
  },
  share_url: "https://content.example.net/a/s3cr3t-slug",
};

describe("artifacts service", () => {
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

  it("listArtifacts GETs /api/artifacts with the bearer token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, [artifact]));
    vi.stubGlobal("fetch", fetchMock);

    await expect(listArtifacts()).resolves.toEqual([artifact]);

    expect(calledUrl(fetchMock)).toMatch(/\/api\/artifacts$/);
    const init = calledInit(fetchMock);
    expect(init.method).toBe("GET");
    expect(authHeader(init)).toBe("Bearer access-token");
  });

  it("createViewLink POSTs /api/artifacts/{id}/view-link and returns the minted url", async () => {
    const link = {
      url: "https://content.example.net/a/s3cr3t-slug?sig=abc",
      expires_at: "2026-10-18T12:00:00Z",
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, link));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createViewLink(7)).resolves.toEqual(link);

    expect(calledUrl(fetchMock)).toMatch(/\/api\/artifacts\/7\/view-link$/);
    expect(calledInit(fetchMock).method).toBe("POST");
  });

  it("getArtifactContent GETs /api/artifacts/{id}/content", async () => {
    const body = { version: 2, content_type: "markdown", content: "# Hi" };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, body));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getArtifactContent(7)).resolves.toEqual(body);

    expect(calledUrl(fetchMock)).toMatch(/\/api\/artifacts\/7\/content$/);
    expect(calledInit(fetchMock).method).toBe("GET");
  });

  it("setArtifactVisibility POSTs the chosen visibility", async () => {
    const updated = { ...artifact, visibility: "unlisted" };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, updated));
    vi.stubGlobal("fetch", fetchMock);

    await expect(setArtifactVisibility(7, "unlisted")).resolves.toEqual(
      updated,
    );

    expect(calledUrl(fetchMock)).toMatch(/\/api\/artifacts\/7\/visibility$/);
    const init = calledInit(fetchMock);
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({ visibility: "unlisted" });
  });

  it("deleteArtifact DELETEs /api/artifacts/{id}", async () => {
    const body = { message: "Artifact deleted", deleted_id: "7" };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, body));
    vi.stubGlobal("fetch", fetchMock);

    await expect(deleteArtifact(7)).resolves.toEqual(body);

    expect(calledUrl(fetchMock)).toMatch(/\/api\/artifacts\/7$/);
    expect(calledInit(fetchMock).method).toBe("DELETE");
  });

  it("rejects with ApiError carrying the backend detail", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(404, { detail: "Artifact not found" }));
    vi.stubGlobal("fetch", fetchMock);

    const failure = createViewLink(99);
    await expect(failure).rejects.toBeInstanceOf(ApiError);
    await expect(failure).rejects.toMatchObject({
      status: 404,
      detail: "Artifact not found",
    });
  });
});
