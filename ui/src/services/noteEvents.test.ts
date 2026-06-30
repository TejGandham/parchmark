import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { setAuthHooks } from "./http";
import { openNoteEventStream, type NoteEvent } from "./noteEvents";

/** Build a 200 SSE response whose body streams the given chunks then closes. */
function sseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

/** Build a 200 SSE response whose body emits one chunk and never closes. */
function openSseResponse(firstChunk: string): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(firstChunk));
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

/** Resolve the RequestInit the stubbed fetch was called with. */
function calledInit(fetchMock: ReturnType<typeof vi.fn>): RequestInit {
  return (fetchMock.mock.calls[0][1] ?? {}) as RequestInit;
}

describe("openNoteEventStream", () => {
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

  it("parses data frames into note events and ignores heartbeat/blank frames", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        sseResponse([
          ":heartbeat\n\n",
          'data: {"kind":"created","note_id":"abc"}\n\n',
          'data: {"kind":"updated","note_id":123}\n\n',
          "\n\n",
          'data: {"kind":"deleted","note_id":"abc"}\n\n',
        ]),
      );
    vi.stubGlobal("fetch", fetchMock);

    const events: NoteEvent[] = [];
    openNoteEventStream({ onEvent: (event) => events.push(event) });

    await vi.waitFor(() => expect(events).toHaveLength(3));
    expect(events).toEqual([
      { kind: "created", note_id: "abc" },
      { kind: "updated", note_id: "123" },
      { kind: "deleted", note_id: "abc" },
    ]);
  });

  it("handles data frames split across read chunks", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        sseResponse(['data: {"kind":"crea', 'ted","note_id":"x"}\n\n']),
      );
    vi.stubGlobal("fetch", fetchMock);

    const events: NoteEvent[] = [];
    openNoteEventStream({ onEvent: (event) => events.push(event) });

    await vi.waitFor(() => expect(events).toHaveLength(1));
    expect(events[0]).toEqual({ kind: "created", note_id: "x" });
  });

  it("ignores malformed data payloads without throwing or emitting", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        sseResponse([
          "data: not-json\n\n",
          'data: {"note_id":"no-kind"}\n\n',
          'data: {"kind":"created","note_id":"ok"}\n\n',
        ]),
      );
    vi.stubGlobal("fetch", fetchMock);

    const events: NoteEvent[] = [];
    const onError = vi.fn();
    openNoteEventStream({ onEvent: (event) => events.push(event), onError });

    await vi.waitFor(() => expect(events).toHaveLength(1));
    expect(events[0]).toEqual({ kind: "created", note_id: "ok" });
    expect(onError).not.toHaveBeenCalled();
  });

  it("sends the bearer token when opening the stream", async () => {
    const fetchMock = vi.fn().mockResolvedValue(sseResponse([]));
    vi.stubGlobal("fetch", fetchMock);

    openNoteEventStream({ onEvent: vi.fn() });

    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const headers = new Headers(
      calledInit(fetchMock).headers as HeadersInit | undefined,
    );
    expect(headers.get("Authorization")).toBe("Bearer access-token");
  });

  it("aborts the underlying request cleanly on close without surfacing an error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        openSseResponse('data: {"kind":"created","note_id":"a"}\n\n'),
      );
    vi.stubGlobal("fetch", fetchMock);

    const events: NoteEvent[] = [];
    const onError = vi.fn();
    const handle = openNoteEventStream({
      onEvent: (event) => events.push(event),
      onError,
    });

    await vi.waitFor(() => expect(events).toHaveLength(1));
    const signal = calledInit(fetchMock).signal as AbortSignal;
    expect(signal.aborted).toBe(false);

    handle.close();
    expect(signal.aborted).toBe(true);
    expect(onError).not.toHaveBeenCalled();
  });

  it("does not open the stream when an already-aborted signal is supplied", async () => {
    const fetchMock = vi.fn().mockResolvedValue(sseResponse([]));
    vi.stubGlobal("fetch", fetchMock);
    const controller = new AbortController();
    controller.abort();

    openNoteEventStream({ onEvent: vi.fn() }, { signal: controller.signal });

    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect((calledInit(fetchMock).signal as AbortSignal).aborted).toBe(true);
  });

  it("surfaces an open failure to onError", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "stream boom" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const onError = vi.fn();
    openNoteEventStream({ onEvent: vi.fn(), onError });

    await vi.waitFor(() => expect(onError).toHaveBeenCalledTimes(1));
    expect(onError.mock.calls[0][0]).toMatchObject({ status: 500 });
  });
});
