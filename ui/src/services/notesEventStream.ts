import {
  EventStreamContentType,
  fetchEventSource,
} from '@microsoft/fetch-event-source';
import { API_BASE_URL } from '../config/constants';
import { useAuthStore } from '../features/auth/store';

export type NoteEventPayload = {
  kind: string;
  note_id: string;
};

export type NoteEventCallback = (event: NoteEventPayload) => void;
export type NoteEventDispose = () => void;
export type NoteEventStreamOptions = {
  onOpen?: () => void;
};

const NOTE_EVENTS_PATH = '/notes/events';
const INITIAL_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 30000;
const STABLE_STREAM_RESET_MS = 30000;

class AuthFailureError extends Error {
  constructor() {
    super('Notes event stream authentication failed');
  }
}

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

const validateEventStreamResponse = (response: Response): void => {
  if (response.status === 401) {
    throw new AuthFailureError();
  }

  if (response.status >= 500) {
    throw new Error(`Retryable notes event stream status: ${response.status}`);
  }

  const contentType = response.headers.get('content-type');

  if (!contentType?.startsWith(EventStreamContentType)) {
    throw new Error(
      `Expected content-type to be ${EventStreamContentType}, Actual: ${contentType}`
    );
  }
};

export const subscribe = (
  callback: NoteEventCallback,
  options: NoteEventStreamOptions = {}
): NoteEventDispose => {
  let disposed = false;
  let activeController: AbortController | undefined;
  let reconnectTimer: ReturnType<typeof window.setTimeout> | undefined;
  let stableStreamTimer: ReturnType<typeof window.setTimeout> | undefined;
  let nextReconnectDelayMs = INITIAL_RECONNECT_DELAY_MS;
  let authRefreshAttempted = false;
  let logoutStarted = false;
  let unsubscribeAuth: (() => void) | undefined;

  const clearReconnectTimer = () => {
    if (reconnectTimer !== undefined) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = undefined;
    }
  };

  const clearStableStreamTimer = () => {
    if (stableStreamTimer !== undefined) {
      window.clearTimeout(stableStreamTimer);
      stableStreamTimer = undefined;
    }
  };

  const takeReconnectDelay = () => {
    const delay = nextReconnectDelayMs;
    nextReconnectDelayMs = Math.min(
      nextReconnectDelayMs * 2,
      MAX_RECONNECT_DELAY_MS
    );
    return delay;
  };

  const markStreamOpen = () => {
    authRefreshAttempted = false;
    clearStableStreamTimer();
    stableStreamTimer = window.setTimeout(() => {
      nextReconnectDelayMs = INITIAL_RECONNECT_DELAY_MS;
      stableStreamTimer = undefined;
    }, STABLE_STREAM_RESET_MS);
    options.onOpen?.();
  };

  const unsubscribeFromAuth = () => {
    unsubscribeAuth?.();
    unsubscribeAuth = undefined;
  };

  const teardownStream = () => {
    if (disposed) {
      return;
    }

    disposed = true;
    clearReconnectTimer();
    clearStableStreamTimer();
    activeController?.abort();
    unsubscribeFromAuth();
  };

  const stopAndLogout = () => {
    if (logoutStarted) {
      return;
    }

    logoutStarted = true;
    teardownStream();
    void useAuthStore
      .getState()
      .actions.logout()
      .catch(() => undefined);
  };

  const handleAuthFailure = async () => {
    if (disposed) {
      return;
    }

    clearStableStreamTimer();

    if (authRefreshAttempted) {
      stopAndLogout();
      return;
    }

    authRefreshAttempted = true;
    const refreshed = await useAuthStore
      .getState()
      .actions.refreshTokens()
      .catch(() => false);

    if (disposed) {
      return;
    }

    if (!refreshed) {
      stopAndLogout();
      return;
    }

    nextReconnectDelayMs = INITIAL_RECONNECT_DELAY_MS;
    startStream();
  };

  const scheduleReconnect = () => {
    if (disposed) {
      return;
    }

    clearStableStreamTimer();
    const delay = takeReconnectDelay();
    reconnectTimer = window.setTimeout(startStream, delay);
  };

  const handleStreamFailure = (error: unknown) => {
    if (error instanceof AuthFailureError) {
      void handleAuthFailure();
      return;
    }

    scheduleReconnect();
  };

  const startStream = () => {
    if (disposed) {
      return;
    }

    clearReconnectTimer();
    activeController = new AbortController();

    void fetchEventSource(`${API_BASE_URL}${NOTE_EVENTS_PATH}`, {
      headers: getAuthHeaders(),
      signal: activeController.signal,
      fetch(input, init) {
        return fetch(input, {
          ...init,
          headers: applyAuthHeader(init?.headers),
        });
      },
      async onopen(response) {
        validateEventStreamResponse(response);

        if (!disposed) {
          markStreamOpen();
        }
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
      onerror(error) {
        throw error;
      },
    }).then(scheduleReconnect, handleStreamFailure);
  };

  unsubscribeAuth = useAuthStore.subscribe((state, previousState) => {
    if (previousState.isAuthenticated && !state.isAuthenticated) {
      teardownStream();
    }
  });

  startStream();

  return teardownStream;
};
