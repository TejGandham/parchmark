import { fetchEventSource } from '@microsoft/fetch-event-source';
import { API_BASE_URL } from '../config/constants';
import { useAuthStore } from '../features/auth/store';

export type NoteEventPayload = {
  kind: string;
  note_id: string;
};

export type NoteEventCallback = (event: NoteEventPayload) => void;
export type NoteEventDispose = () => void;

const NOTE_EVENTS_PATH = '/notes/events';

const getAuthHeaders = (): Record<string, string> => {
  const token = useAuthStore.getState().token;
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const applyAuthHeader = (headers: HeadersInit | undefined): Headers => {
  const nextHeaders = new Headers(headers);
  const token = useAuthStore.getState().token;

  if (token) {
    nextHeaders.set('Authorization', `Bearer ${token}`);
  } else {
    nextHeaders.delete('Authorization');
  }

  return nextHeaders;
};

const isNoteEventPayload = (payload: unknown): payload is NoteEventPayload => {
  if (!payload || typeof payload !== 'object') {
    return false;
  }

  const event = payload as Partial<NoteEventPayload>;
  return typeof event.kind === 'string' && typeof event.note_id === 'string';
};

export const subscribe = (callback: NoteEventCallback): NoteEventDispose => {
  const controller = new AbortController();
  let disposed = false;

  void fetchEventSource(`${API_BASE_URL}${NOTE_EVENTS_PATH}`, {
    headers: getAuthHeaders(),
    signal: controller.signal,
    fetch(input, init) {
      return fetch(input, {
        ...init,
        headers: applyAuthHeader(init?.headers),
      });
    },
    onmessage(message) {
      if (disposed) {
        return;
      }

      let payload: unknown;
      try {
        payload = JSON.parse(message.data) as unknown;
      } catch {
        return;
      }

      if (isNoteEventPayload(payload)) {
        callback(payload);
      }
    },
  });

  return () => {
    disposed = true;
    controller.abort();
  };
};
