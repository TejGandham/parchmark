import { getCurrentInstance, onUnmounted, readonly, ref } from "vue";

import {
  openNoteEventStream,
  type NoteEvent,
  type NoteEventStreamHandle,
} from "../../services/noteEvents";

/** Options for {@link useNoteEvents}. */
export interface UseNoteEventsOptions {
  /** Called for each note-change event while the stream is open. */
  onEvent: (event: NoteEvent) => void;
}

/**
 * Composable that manages the lifecycle of the authenticated note-events
 * stream. It does not auto-connect: the caller decides when to {@link start}
 * (e.g. after the initial notes load, while authenticated) and {@link stop}
 * (on logout). The stream is also torn down automatically on component unmount.
 *
 * Unlike `useAuth`/`useNotes`, this is intentionally NOT a module singleton —
 * each caller owns one stream bound to its own component lifetime.
 */
export function useNoteEvents(options: UseNoteEventsOptions) {
  const connected = ref(false);
  const error = ref<unknown>(null);

  let handle: NoteEventStreamHandle | null = null;

  /** Open the stream if it is not already open. Idempotent. */
  function start(): void {
    if (handle) {
      return;
    }
    error.value = null;
    handle = openNoteEventStream({
      onEvent: options.onEvent,
      onError: (caught) => {
        // A stream error must not clear the visible notes list; surface it as
        // non-blocking status and mark the stream disconnected.
        error.value = caught;
        connected.value = false;
      },
    });
    connected.value = true;
  }

  /** Tear the stream down if it is open. Idempotent. */
  function stop(): void {
    handle?.close();
    handle = null;
    connected.value = false;
  }

  // Tear down on unmount when used inside a component setup. Guarded so direct
  // (non-component) callers in tests don't trigger a lifecycle-hook warning.
  if (getCurrentInstance()) {
    onUnmounted(stop);
  }

  return {
    connected: readonly(connected),
    error: readonly(error),
    start,
    stop,
  };
}
