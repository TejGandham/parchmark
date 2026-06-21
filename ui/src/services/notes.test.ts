import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, resetAuthHooks, setAuthHooks } from "./http";
import { createNote, listNotes, updateNote, type NoteDTO } from "./notes";

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

/** A representative NoteResponse[] body with all fields populated. */
const sampleNotes: NoteDTO[] = [
  {
    id: "note-1",
    title: "First note",
    content: "# First note\n\nHello.",
    tags: ["draft", "work"],
    createdAt: "2025-01-01T00:00:00.000Z",
    updatedAt: "2025-01-02T00:00:00.000Z",
  },
  {
    id: "note-2",
    title: "Second note",
    content: "# Second note\n\nWorld.",
    tags: [],
    createdAt: "2025-01-03T00:00:00.000Z",
    updatedAt: "2025-01-04T00:00:00.000Z",
  },
];

describe("listNotes", () => {
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

  it("issues GET to /api/notes/ with the bearer token from auth hooks", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, sampleNotes));
    vi.stubGlobal("fetch", fetchMock);

    await listNotes();

    expect(calledUrl(fetchMock)).toContain("/api/notes/");
    const init = calledInit(fetchMock);
    expect(init.method).toBe("GET");
    expect(authHeader(init)).toBe("Bearer access-token");
  });

  it("resolves to the NoteResponse[] body unchanged (no stripping, no renaming)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, sampleNotes));
    vi.stubGlobal("fetch", fetchMock);

    const result = await listNotes();

    expect(result).toEqual(sampleNotes);
    expect(result).toHaveLength(2);
    // Every field, including title and tags, is passed through verbatim.
    expect(result[0]).toHaveProperty("title");
    expect(result[0]).toHaveProperty("tags");
    expect(result[0].title).toBe("First note");
    expect(result[0].tags).toEqual(["draft", "work"]);
  });

  it("rejects with ApiError carrying backend { detail } on non-2xx", async () => {
    // 500 avoids the 401 refresh-and-retry path in http.ts, keeping the test
    // focused on error propagation from the HTTP layer.
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(500, { detail: "boom" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(listNotes()).rejects.toMatchObject({
      status: 500,
      detail: "boom",
    });
    await expect(listNotes()).rejects.toBeInstanceOf(ApiError);
  });
});

describe("createNote", () => {
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

  it("POSTs to /api/notes/ with the supplied body and bearer token", async () => {
    const created = sampleNotes[0];
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, created));
    vi.stubGlobal("fetch", fetchMock);

    const payload = { content: "# Untitled\n\n", tags: ["draft"] };
    const result = await createNote(payload);

    expect(calledUrl(fetchMock)).toContain("/api/notes/");
    const init = calledInit(fetchMock);
    expect(init.method).toBe("POST");
    expect(authHeader(init)).toBe("Bearer access-token");
    expect(JSON.parse(String(init.body))).toEqual(payload);
    expect(result).toEqual(created);
  });

  it("rejects with ApiError carrying backend { detail } on create failure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(422, { detail: "content too short" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createNote({ content: "" })).rejects.toMatchObject({
      status: 422,
      detail: "content too short",
    });
  });
});

describe("updateNote", () => {
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

  it("PUTs to /api/notes/{note_id} with the supplied body and bearer token", async () => {
    const updated = {
      ...sampleNotes[0],
      content: "# Updated\n\nSaved.",
      updatedAt: "2026-06-21T10:30:00.000Z",
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, updated));
    vi.stubGlobal("fetch", fetchMock);

    const payload = { content: "# Updated\n\nSaved." };
    const result = await updateNote("note-1", payload);

    expect(calledUrl(fetchMock)).toContain("/api/notes/note-1");
    const init = calledInit(fetchMock);
    expect(init.method).toBe("PUT");
    expect(authHeader(init)).toBe("Bearer access-token");
    expect(JSON.parse(String(init.body))).toEqual(payload);
    expect(result).toEqual(updated);
  });

  it("rejects with ApiError carrying backend { detail } on update failure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(404, { detail: "Note not found" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      updateNote("missing", { content: "# Lost" }),
    ).rejects.toMatchObject({
      status: 404,
      detail: "Note not found",
    });
  });
});
