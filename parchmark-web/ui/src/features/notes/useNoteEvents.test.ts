import { mount } from "@vue/test-utils";
import { defineComponent } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type {
  NoteEvent,
  NoteEventStreamHandlers,
} from "../../services/noteEvents";
import { useNoteEvents } from "./useNoteEvents";

const { openNoteEventStreamMock } = vi.hoisted(() => ({
  openNoteEventStreamMock: vi.fn(),
}));

vi.mock("../../services/noteEvents", () => ({
  openNoteEventStream: openNoteEventStreamMock,
}));

/** Read back the handlers the composable passed to the mocked service. */
function passedHandlers(call = 0): NoteEventStreamHandlers {
  return openNoteEventStreamMock.mock.calls[call][0] as NoteEventStreamHandlers;
}

describe("useNoteEvents", () => {
  beforeEach(() => {
    openNoteEventStreamMock.mockReset();
    openNoteEventStreamMock.mockReturnValue({ close: vi.fn() });
  });

  it("does not connect until start is called", () => {
    const { connected } = useNoteEvents({ onEvent: vi.fn() });

    expect(connected.value).toBe(false);
    expect(openNoteEventStreamMock).not.toHaveBeenCalled();
  });

  it("opens the stream and marks connected on start", () => {
    const { connected, start } = useNoteEvents({ onEvent: vi.fn() });

    start();

    expect(openNoteEventStreamMock).toHaveBeenCalledTimes(1);
    expect(connected.value).toBe(true);
  });

  it("does not open a second stream when start is called twice", () => {
    const { start } = useNoteEvents({ onEvent: vi.fn() });

    start();
    start();

    expect(openNoteEventStreamMock).toHaveBeenCalledTimes(1);
  });

  it("forwards parsed events to the provided onEvent handler", () => {
    const onEvent = vi.fn();
    const { start } = useNoteEvents({ onEvent });

    start();
    const event: NoteEvent = { kind: "created", note_id: "n1" };
    passedHandlers().onEvent(event);

    expect(onEvent).toHaveBeenCalledWith(event);
  });

  it("closes the stream and disconnects on stop", () => {
    const handle = { close: vi.fn() };
    openNoteEventStreamMock.mockReturnValue(handle);
    const { connected, start, stop } = useNoteEvents({ onEvent: vi.fn() });

    start();
    stop();

    expect(handle.close).toHaveBeenCalledTimes(1);
    expect(connected.value).toBe(false);
  });

  it("stop is a no-op when the stream was never started", () => {
    const { stop, connected } = useNoteEvents({ onEvent: vi.fn() });

    expect(() => stop()).not.toThrow();
    expect(connected.value).toBe(false);
  });

  it("records a stream error as non-blocking status without clearing handlers", () => {
    const { connected, error, start } = useNoteEvents({ onEvent: vi.fn() });

    start();
    const boom = new Error("stream down");
    passedHandlers().onError?.(boom);

    expect(error.value).toBe(boom);
    expect(connected.value).toBe(false);
  });

  it("tears the stream down on component unmount", () => {
    const handle = { close: vi.fn() };
    openNoteEventStreamMock.mockReturnValue(handle);

    const Host = defineComponent({
      setup() {
        const events = useNoteEvents({ onEvent: vi.fn() });
        events.start();
        return () => null;
      },
    });

    const wrapper = mount(Host);
    expect(handle.close).not.toHaveBeenCalled();

    wrapper.unmount();
    expect(handle.close).toHaveBeenCalledTimes(1);
  });
});
