import { requestStream } from "./http";

/** Path of the backend Server-Sent Events stream, relative to the API base. */
export const NOTE_EVENTS_PATH = "/notes/events";

/** Change kinds the backend emits for a note. Any future kind is also allowed. */
export type NoteEventKind = "created" | "updated" | "deleted";

/**
 * A single note-change event parsed from an SSE `data:` frame. Mirrors the
 * backend payload `{ kind, note_id }`; `note_id` is normalized to a string.
 */
export interface NoteEvent {
  kind: NoteEventKind | (string & {});
  note_id: string;
}

/** Callbacks invoked as the stream produces events or fails. */
export interface NoteEventStreamHandlers {
  /** Called once per parsed note event (heartbeats are filtered out). */
  onEvent: (event: NoteEvent) => void;
  /** Called when the stream fails for any reason other than an explicit close. */
  onError?: (error: unknown) => void;
}

/** Handle returned by {@link openNoteEventStream} for explicit teardown. */
export interface NoteEventStreamHandle {
  /** Abort the underlying request and stop reading the stream. */
  close: () => void;
}

/**
 * Parse one SSE frame (the text between blank-line separators) into a
 * {@link NoteEvent}, or `null` when the frame carries no usable note event.
 * Comment frames (lines starting with `:`, e.g. the `:heartbeat` keep-alive),
 * blank frames, and non-`data` fields are ignored, as are malformed payloads.
 */
function parseFrame(frame: string): NoteEvent | null {
  const dataLines: string[] = [];

  for (const rawLine of frame.split("\n")) {
    const line = rawLine.replace(/\r$/, "");
    if (line === "" || line.startsWith(":")) {
      continue; // blank line or comment frame (heartbeat) — ignore
    }
    if (line.startsWith("data:")) {
      // Per the SSE spec, strip a single optional leading space after the colon.
      dataLines.push(line.slice(5).replace(/^ /, ""));
    }
    // Other SSE fields (event:, id:, retry:) are not used by this stream.
  }

  if (dataLines.length === 0) {
    return null;
  }

  try {
    const parsed = JSON.parse(dataLines.join("\n")) as {
      kind?: unknown;
      note_id?: unknown;
    };
    if (typeof parsed.kind !== "string") {
      return null;
    }
    if (
      typeof parsed.note_id !== "string" &&
      typeof parsed.note_id !== "number"
    ) {
      return null;
    }
    return { kind: parsed.kind, note_id: String(parsed.note_id) };
  } catch {
    return null; // non-JSON data payload — ignore rather than throw
  }
}

/**
 * Read an open SSE response body, splitting it into frames on the blank-line
 * separator and forwarding each parsed {@link NoteEvent} to `onEvent`. Resolves
 * when the stream ends or is aborted; surfaces non-abort failures to `onError`.
 */
async function consumeStream(
  response: Response,
  handlers: NoteEventStreamHandlers,
  signal: AbortSignal,
): Promise<void> {
  if (!response.body) {
    return; // no readable body (shouldn't happen for a 200 stream) — nothing to do
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });

      let separator = buffer.indexOf("\n\n");
      while (separator !== -1) {
        const frame = buffer.slice(0, separator);
        buffer = buffer.slice(separator + 2);
        const event = parseFrame(frame);
        if (event) {
          handlers.onEvent(event);
        }
        separator = buffer.indexOf("\n\n");
      }
    }
  } catch (error) {
    if (!signal.aborted) {
      handlers.onError?.(error);
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Open the authenticated note-events stream and forward parsed change events to
 * the supplied handlers. Uses {@link requestStream} so the bearer token and the
 * single refresh-and-retry policy from `http.ts` apply to the stream open. The
 * returned handle's {@link NoteEventStreamHandle.close} aborts the request and
 * stops reading; passing an external `signal` aborts it too.
 */
export function openNoteEventStream(
  handlers: NoteEventStreamHandlers,
  options: { signal?: AbortSignal } = {},
): NoteEventStreamHandle {
  const controller = new AbortController();

  if (options.signal) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      options.signal.addEventListener("abort", () => controller.abort(), {
        once: true,
      });
    }
  }

  const run = async (): Promise<void> => {
    try {
      const response = await requestStream(NOTE_EVENTS_PATH, {
        signal: controller.signal,
      });
      await consumeStream(response, handlers, controller.signal);
    } catch (error) {
      if (!controller.signal.aborted) {
        handlers.onError?.(error);
      }
    }
  };

  void run();

  return {
    close: () => controller.abort(),
  };
}
