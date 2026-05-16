import { fetchEventSource } from '@microsoft/fetch-event-source';
import { subscribe } from '../../services/notesEventStream';
import { useAuthStore } from '../../features/auth/store';

vi.mock('@microsoft/fetch-event-source', () => ({
  fetchEventSource: vi.fn(() => new Promise(() => undefined)),
}));

vi.mock('../../features/auth/store', () => ({
  useAuthStore: {
    getState: vi.fn(() => ({ token: null })),
  },
}));

describe('notesEventStream', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    (useAuthStore.getState as Mock).mockReturnValue({ token: null });
  });

  it('subscribes to notes events with the REST bearer Authorization header', () => {
    (useAuthStore.getState as Mock).mockReturnValue({
      token: 'sse-token-123',
    });

    subscribe(vi.fn());

    expect(fetchEventSource).toHaveBeenCalledWith(
      '/api/notes/events',
      expect.objectContaining({
        headers: {
          Authorization: 'Bearer sse-token-123',
        },
        signal: expect.any(AbortSignal),
      })
    );
  });

  it('reads the current REST bearer token for each transport fetch attempt', () => {
    (useAuthStore.getState as Mock).mockReturnValueOnce({
      token: 'initial-token',
    });
    (useAuthStore.getState as Mock).mockReturnValueOnce({
      token: 'refreshed-token',
    });

    subscribe(vi.fn());

    const options = (fetchEventSource as Mock).mock.calls[0][1];
    options.fetch('/api/notes/events', { headers: {} });

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/notes/events',
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    );
    const headers = (global.fetch as Mock).mock.calls[0][1].headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer refreshed-token');
  });

  it('delivers one callback per parsed note event payload', () => {
    const callback = vi.fn();

    subscribe(callback);

    const options = (fetchEventSource as Mock).mock.calls[0][1];
    options.onmessage({ data: '{"kind":"created","note_id":"note-1"}' });
    options.onmessage({ data: '{"kind":"updated","note_id":"note-2"}' });

    expect(callback).toHaveBeenCalledTimes(2);
    expect(callback).toHaveBeenNthCalledWith(1, {
      kind: 'created',
      note_id: 'note-1',
    });
    expect(callback).toHaveBeenNthCalledWith(2, {
      kind: 'updated',
      note_id: 'note-2',
    });
  });

  it('ignores malformed and non-note event payloads', () => {
    const callback = vi.fn();

    subscribe(callback);

    const options = (fetchEventSource as Mock).mock.calls[0][1];
    options.onmessage({ data: 'not-json' });
    options.onmessage({ data: '{"kind":"updated"}' });
    options.onmessage({ data: '{"kind":"updated","note_id":123}' });

    expect(callback).not.toHaveBeenCalled();
  });

  it('aborts and suppresses later callback delivery after dispose', () => {
    const callback = vi.fn();
    const dispose = subscribe(callback);
    const options = (fetchEventSource as Mock).mock.calls[0][1];

    options.onmessage({ data: '{"kind":"deleted","note_id":"note-before"}' });
    dispose();
    options.onmessage({ data: '{"kind":"updated","note_id":"note-after"}' });

    expect(options.signal.aborted).toBe(true);
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith({
      kind: 'deleted',
      note_id: 'note-before',
    });
  });
});
