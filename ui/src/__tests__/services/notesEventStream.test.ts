import { fetchEventSource } from '@microsoft/fetch-event-source';
import { subscribe } from '../../services/notesEventStream';
import { useAuthStore } from '../../features/auth/store';

vi.mock('@microsoft/fetch-event-source', () => ({
  EventStreamContentType: 'text/event-stream',
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
    (fetchEventSource as Mock).mockImplementation(
      () => new Promise(() => undefined)
    );
    global.fetch = vi.fn();
    (useAuthStore.getState as Mock).mockReturnValue({ token: null });
  });

  afterEach(() => {
    vi.useRealTimers();
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

  it('notifies once per stream open for initial connect and reconnect recovery', async () => {
    const onOpen = vi.fn();

    const dispose = subscribe(vi.fn(), { onOpen });

    const options = (fetchEventSource as Mock).mock.calls[0][1];
    const response = new Response(null, {
      headers: { 'content-type': 'text/event-stream' },
    });

    await options.onopen(response);
    await options.onopen(response);

    expect(onOpen).toHaveBeenCalledTimes(2);
    dispose();
  });

  it('reconnects after stream close with exponential backoff timing', async () => {
    vi.useFakeTimers();
    (fetchEventSource as Mock).mockImplementation(() => Promise.resolve());

    const dispose = subscribe(vi.fn());
    await vi.advanceTimersByTimeAsync(0);

    const expectedAttemptTimes = [1000, 3000, 7000, 15000, 31000, 61000];
    let elapsedMs = 0;

    for (const [index, attemptTimeMs] of expectedAttemptTimes.entries()) {
      await vi.advanceTimersByTimeAsync(attemptTimeMs - elapsedMs - 1);
      expect(fetchEventSource).toHaveBeenCalledTimes(index + 1);

      await vi.advanceTimersByTimeAsync(1);
      expect(fetchEventSource).toHaveBeenCalledTimes(index + 2);
      elapsedMs = attemptTimeMs;
    }

    dispose();
  });

  it('caps reconnect delay at thirty seconds after repeated failures', async () => {
    vi.useFakeTimers();
    (fetchEventSource as Mock).mockImplementation(() =>
      Promise.reject(new Error('network down'))
    );

    const dispose = subscribe(vi.fn());
    await vi.advanceTimersByTimeAsync(0);

    for (const delayMs of [1000, 2000, 4000, 8000, 16000, 30000, 30000]) {
      const expectedCallsBeforeDelay = (fetchEventSource as Mock).mock.calls
        .length;

      await vi.advanceTimersByTimeAsync(delayMs - 1);
      expect(fetchEventSource).toHaveBeenCalledTimes(expectedCallsBeforeDelay);

      await vi.advanceTimersByTimeAsync(1);
      expect(fetchEventSource).toHaveBeenCalledTimes(
        expectedCallsBeforeDelay + 1
      );
    }

    dispose();
  });

  it('reconnects after retryable 5xx stream-open responses', async () => {
    vi.useFakeTimers();
    (fetchEventSource as Mock).mockImplementation((_input, options) =>
      options.onopen(
        new Response(null, {
          status: 503,
          headers: { 'content-type': 'text/event-stream' },
        })
      )
    );

    const dispose = subscribe(vi.fn());
    await vi.advanceTimersByTimeAsync(999);
    expect(fetchEventSource).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(1);
    expect(fetchEventSource).toHaveBeenCalledTimes(2);
    dispose();
  });

  it('resets reconnect backoff after thirty seconds of stable open time', async () => {
    vi.useFakeTimers();
    const openStreams: Array<() => void> = [];
    (fetchEventSource as Mock).mockImplementation(
      () =>
        new Promise<void>((resolve) => {
          openStreams.push(resolve);
        })
    );

    const dispose = subscribe(vi.fn());
    openStreams[0]();
    await vi.advanceTimersByTimeAsync(1000);
    expect(fetchEventSource).toHaveBeenCalledTimes(2);

    const secondAttempt = (fetchEventSource as Mock).mock.calls[1][1];
    await secondAttempt.onopen(
      new Response(null, {
        headers: { 'content-type': 'text/event-stream' },
      })
    );
    await vi.advanceTimersByTimeAsync(30000);

    openStreams[1]();
    await vi.advanceTimersByTimeAsync(999);
    expect(fetchEventSource).toHaveBeenCalledTimes(2);

    await vi.advanceTimersByTimeAsync(1);
    expect(fetchEventSource).toHaveBeenCalledTimes(3);
    dispose();
  });

  it('refreshes tokens before reconnecting after a 401 stream response', async () => {
    vi.useFakeTimers();
    let token = 'expired-token';
    let resolveRefresh: (success: boolean) => void = () => undefined;
    const refreshTokens = vi.fn(
      () =>
        new Promise<boolean>((resolve) => {
          resolveRefresh = resolve;
        })
    );
    const logout = vi.fn().mockResolvedValue(undefined);
    (useAuthStore.getState as Mock).mockImplementation(() => ({
      token,
      actions: { refreshTokens, logout },
    }));
    (fetchEventSource as Mock)
      .mockImplementationOnce((_input, options) =>
        options.onopen(new Response(null, { status: 401 }))
      )
      .mockImplementation(() => new Promise(() => undefined));

    const dispose = subscribe(vi.fn());
    await vi.advanceTimersByTimeAsync(0);

    expect(refreshTokens).toHaveBeenCalledTimes(1);
    expect(fetchEventSource).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(60000);
    expect(fetchEventSource).toHaveBeenCalledTimes(1);

    token = 'fresh-token';
    resolveRefresh(true);
    await vi.advanceTimersByTimeAsync(0);

    expect(fetchEventSource).toHaveBeenCalledTimes(2);
    expect((fetchEventSource as Mock).mock.calls[1][1].headers).toEqual({
      Authorization: 'Bearer fresh-token',
    });
    expect(logout).not.toHaveBeenCalled();
    dispose();
  });

  it('resets backoff after successful auth refresh reconnects with a new bearer token', async () => {
    vi.useFakeTimers();
    let token = 'expired-token';
    const refreshTokens = vi.fn(async () => {
      token = 'fresh-token';
      return true;
    });
    const logout = vi.fn().mockResolvedValue(undefined);
    (useAuthStore.getState as Mock).mockImplementation(() => ({
      token,
      actions: { refreshTokens, logout },
    }));
    (fetchEventSource as Mock)
      .mockImplementationOnce(() => Promise.reject(new Error('network down')))
      .mockImplementationOnce((_input, options) =>
        options.onopen(new Response(null, { status: 401 }))
      )
      .mockImplementationOnce(() => Promise.resolve())
      .mockImplementation(() => new Promise(() => undefined));

    const dispose = subscribe(vi.fn());
    await vi.advanceTimersByTimeAsync(0);
    await vi.advanceTimersByTimeAsync(1000);
    await vi.advanceTimersByTimeAsync(0);

    expect(refreshTokens).toHaveBeenCalledTimes(1);
    expect(fetchEventSource).toHaveBeenCalledTimes(3);
    expect((fetchEventSource as Mock).mock.calls[2][1].headers).toEqual({
      Authorization: 'Bearer fresh-token',
    });

    await vi.advanceTimersByTimeAsync(999);
    expect(fetchEventSource).toHaveBeenCalledTimes(3);

    await vi.advanceTimersByTimeAsync(1);
    expect(fetchEventSource).toHaveBeenCalledTimes(4);
    expect(logout).not.toHaveBeenCalled();
    dispose();
  });

  it('logs out once and stops reconnecting when auth refresh fails', async () => {
    vi.useFakeTimers();
    const refreshTokens = vi.fn().mockResolvedValue(false);
    const logout = vi.fn().mockResolvedValue(undefined);
    (useAuthStore.getState as Mock).mockReturnValue({
      token: 'expired-token',
      actions: { refreshTokens, logout },
    });
    (fetchEventSource as Mock).mockImplementation((_input, options) =>
      options.onopen(new Response(null, { status: 401 }))
    );

    subscribe(vi.fn());
    await vi.advanceTimersByTimeAsync(0);

    expect(refreshTokens).toHaveBeenCalledTimes(1);
    expect(logout).toHaveBeenCalledTimes(1);
    expect(fetchEventSource).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(60000);
    expect(refreshTokens).toHaveBeenCalledTimes(1);
    expect(logout).toHaveBeenCalledTimes(1);
    expect(fetchEventSource).toHaveBeenCalledTimes(1);
  });

  it('does not refresh forever when a refreshed stream still receives 401', async () => {
    vi.useFakeTimers();
    let token = 'expired-token';
    const refreshTokens = vi.fn(async () => {
      token = 'fresh-token';
      return true;
    });
    const logout = vi.fn().mockResolvedValue(undefined);
    (useAuthStore.getState as Mock).mockImplementation(() => ({
      token,
      actions: { refreshTokens, logout },
    }));
    (fetchEventSource as Mock).mockImplementation((_input, options) =>
      options.onopen(new Response(null, { status: 401 }))
    );

    subscribe(vi.fn());
    await vi.advanceTimersByTimeAsync(0);

    expect(refreshTokens).toHaveBeenCalledTimes(1);
    expect(logout).toHaveBeenCalledTimes(1);
    expect(fetchEventSource).toHaveBeenCalledTimes(2);

    await vi.advanceTimersByTimeAsync(60000);
    expect(refreshTokens).toHaveBeenCalledTimes(1);
    expect(logout).toHaveBeenCalledTimes(1);
    expect(fetchEventSource).toHaveBeenCalledTimes(2);
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
