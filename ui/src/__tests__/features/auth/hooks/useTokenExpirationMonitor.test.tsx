import { vi, Mock } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTokenExpirationMonitor } from '../../../../features/auth/hooks/useTokenExpirationMonitor';
import { useAuthStore } from '../../../../features/auth/store';

// Mock the auth store
vi.mock('../../../../features/auth/store');

describe('useTokenExpirationMonitor', () => {
  let mockCheckTokenExpiration: Mock;

  beforeEach(() => {
    vi.useFakeTimers();
    mockCheckTokenExpiration = vi.fn();

    // Default mock implementation
    (useAuthStore as unknown as Mock).mockImplementation((selector) => {
      const state = {
        token: 'mock-token',
        actions: {
          checkTokenExpiration: mockCheckTokenExpiration,
        },
      };
      return selector ? selector(state) : state;
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('should check token expiration immediately when token exists', () => {
    renderHook(() => useTokenExpirationMonitor());

    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(1);
  });

  it('should set up interval to check token expiration every 3 minutes', () => {
    renderHook(() => useTokenExpirationMonitor());

    // Initial check
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(1);

    // Fast-forward 3 minutes
    act(() => {
      vi.advanceTimersByTime(180000);
    });
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(2);

    // Fast-forward another 3 minutes
    act(() => {
      vi.advanceTimersByTime(180000);
    });
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(3);
  });

  it('should not check expiration when no token exists', () => {
    // Mock store with no token
    (useAuthStore as unknown as Mock).mockImplementation((selector) => {
      const state = {
        token: null,
        actions: {
          checkTokenExpiration: mockCheckTokenExpiration,
        },
      };
      return selector ? selector(state) : state;
    });

    renderHook(() => useTokenExpirationMonitor());

    expect(mockCheckTokenExpiration).not.toHaveBeenCalled();

    // Fast-forward time to ensure no interval calls
    act(() => {
      vi.advanceTimersByTime(360000); // 6 minutes
    });
    expect(mockCheckTokenExpiration).not.toHaveBeenCalled();
  });

  it('should clean up interval on unmount', () => {
    const { unmount } = renderHook(() => useTokenExpirationMonitor());

    // Initial check
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(1);

    // Unmount the hook
    unmount();

    // Fast-forward time after unmount
    act(() => {
      vi.advanceTimersByTime(360000); // 6 minutes
    });

    // Should still only have the initial call
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(1);
  });

  it('should restart interval when token changes', () => {
    const { rerender } = renderHook(() => useTokenExpirationMonitor());

    // Initial check with first token
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(1);

    // Change the token
    (useAuthStore as unknown as Mock).mockImplementation((selector) => {
      const state = {
        token: 'new-token',
        actions: {
          checkTokenExpiration: mockCheckTokenExpiration,
        },
      };
      return selector ? selector(state) : state;
    });

    rerender();

    // Should check again immediately with new token
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(2);

    // Fast-forward to ensure new interval is working
    act(() => {
      vi.advanceTimersByTime(180000);
    });
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(3);
  });

  it('should stop checking when token is removed', () => {
    const { rerender } = renderHook(() => useTokenExpirationMonitor());

    // Initial check
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(1);

    // Remove the token
    (useAuthStore as unknown as Mock).mockImplementation((selector) => {
      const state = {
        token: null,
        actions: {
          checkTokenExpiration: mockCheckTokenExpiration,
        },
      };
      return selector ? selector(state) : state;
    });

    rerender();

    // Fast-forward time
    act(() => {
      vi.advanceTimersByTime(360000); // 6 minutes
    });

    // Should still only have the initial call
    expect(mockCheckTokenExpiration).toHaveBeenCalledTimes(1);
  });
});
