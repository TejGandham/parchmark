import { vi, Mock } from 'vitest';
import { act } from 'react';
import { useAuthStore, AuthState } from '../../../../features/auth/store/auth';
import * as api from '../../../../services/api';
import * as tokenUtils from '../../../../features/auth/utils/tokenUtils';

vi.mock('../../../../services/api');
vi.mock('../../../../features/auth/utils/tokenUtils');

describe('Auth Store', () => {
  let store: AuthState;

  beforeEach(() => {
    // Reset the store before each test
    act(() => {
      useAuthStore.setState({
        isAuthenticated: false,
        user: null,
        token: null,
        refreshToken: null,
        error: null,
        actions: useAuthStore.getState().actions,
      });
    });

    store = useAuthStore.getState();
    vi.clearAllMocks();
  });

  it('should initialize with unauthenticated state', () => {
    expect(store.isAuthenticated).toBe(false);
    expect(store.user).toBeNull();
    expect(store.token).toBeNull();
    expect(store.refreshToken).toBeNull();
    expect(store.error).toBeNull();
  });

  it('should authenticate with valid credentials', async () => {
    const { actions } = store;

    // Mock the successful API call
    (api.login as Mock).mockResolvedValue({
      access_token: 'test-token',
      refresh_token: 'test-refresh-token',
    });

    const success = await actions.login('user', 'password');
    const newState = useAuthStore.getState();

    expect(success).toBe(true);
    expect(newState.isAuthenticated).toBe(true);
    expect(newState.user).toEqual({ username: 'user', password: '' });
    expect(newState.token).toBe('test-token');
    expect(newState.refreshToken).toBe('test-refresh-token');
    expect(newState.error).toBeNull();
  });

  it('should fail authentication with invalid credentials', async () => {
    const { actions } = store;

    // Mock the failed API call
    (api.login as Mock).mockRejectedValue(
      new Error('Invalid username or password')
    );

    const success = await actions.login('user', 'wrongpassword');
    const newState = useAuthStore.getState();

    expect(success).toBe(false);
    expect(newState.isAuthenticated).toBe(false);
    expect(newState.user).toBeNull();
    expect(newState.error).toBe('Invalid username or password');
  });

  it('should handle login error without message', async () => {
    const { actions } = store;

    // Mock the failed API call with error object without message
    (api.login as Mock).mockRejectedValue({});

    const success = await actions.login('user', 'wrongpassword');
    const newState = useAuthStore.getState();

    expect(success).toBe(false);
    expect(newState.isAuthenticated).toBe(false);
    expect(newState.user).toBeNull();
    expect(newState.error).toBe('An unexpected error occurred');
  });

  it('should logout successfully', async () => {
    const { actions } = store;

    // First login
    (api.login as Mock).mockResolvedValue({
      access_token: 'test-token',
      refresh_token: 'test-refresh-token',
    });
    await actions.login('user', 'password');
    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    // Then logout
    actions.logout();
    const newState = useAuthStore.getState();

    expect(newState.isAuthenticated).toBe(false);
    expect(newState.user).toBeNull();
    expect(newState.token).toBeNull();
    expect(newState.refreshToken).toBeNull();
  });

  it('should clear error message', async () => {
    const { actions } = store;

    // First create an error
    (api.login as Mock).mockRejectedValue(
      new Error('Invalid username or password')
    );
    await actions.login('user', 'wrongpassword');
    expect(useAuthStore.getState().error).toBe('Invalid username or password');

    // Then clear the error
    actions.clearError();
    expect(useAuthStore.getState().error).toBeNull();
  });

  describe('refreshTokens', () => {
    it('should refresh tokens successfully with valid refresh token', async () => {
      const { actions } = store;

      // First login to get initial tokens
      (api.login as Mock).mockResolvedValue({
        access_token: 'old-access-token',
        refresh_token: 'old-refresh-token',
      });
      await actions.login('user', 'password');

      // Mock the refresh API call
      (api.refreshToken as Mock).mockResolvedValue({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
      });

      const success = await actions.refreshTokens();
      const newState = useAuthStore.getState();

      expect(success).toBe(true);
      expect(newState.token).toBe('new-access-token');
      expect(newState.refreshToken).toBe('new-refresh-token');
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.error).toBeNull();
      expect(api.refreshToken).toHaveBeenCalledWith('old-refresh-token');
    });

    it('should fail to refresh when no refresh token exists', async () => {
      const { actions } = store;

      // No login, so no refresh token
      const success = await actions.refreshTokens();

      expect(success).toBe(false);
      expect(api.refreshToken).not.toHaveBeenCalled();
    });

    it('should logout when refresh token is invalid', async () => {
      const { actions } = store;

      // First login
      (api.login as Mock).mockResolvedValue({
        access_token: 'old-access-token',
        refresh_token: 'invalid-refresh-token',
      });
      await actions.login('user', 'password');
      expect(useAuthStore.getState().isAuthenticated).toBe(true);

      // Mock failed refresh
      (api.refreshToken as Mock).mockRejectedValue(
        new Error('Could not validate refresh token')
      );

      const success = await actions.refreshTokens();
      const newState = useAuthStore.getState();

      expect(success).toBe(false);
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.token).toBeNull();
      expect(newState.refreshToken).toBeNull();
      expect(newState.user).toBeNull();
    });
  });

  describe('checkTokenExpiration', () => {
    it('should refresh tokens when token is expiring soon', async () => {
      const { actions } = store;

      // First login to set a token
      (api.login as Mock).mockResolvedValue({
        access_token: 'test-token',
        refresh_token: 'test-refresh-token',
      });
      await actions.login('user', 'password');
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().token).toBe('test-token');

      // Mock token as expiring soon
      (tokenUtils.isTokenExpiringSoon as Mock).mockReturnValue(true);

      // Mock successful token refresh
      (api.refreshToken as Mock).mockResolvedValue({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
      });

      // Check token expiration
      await act(async () => {
        actions.checkTokenExpiration();
        // Wait for async refresh to complete
        await new Promise((resolve) => setTimeout(resolve, 0));
      });

      // Should refresh tokens, not logout
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.token).toBe('new-access-token');
      expect(newState.refreshToken).toBe('new-refresh-token');
      expect(api.refreshToken).toHaveBeenCalledWith('test-refresh-token');
    });

    it('should not refresh when token is not expiring soon', async () => {
      const { actions } = store;

      // First login to set a token
      (api.login as Mock).mockResolvedValue({
        access_token: 'test-token',
        refresh_token: 'test-refresh-token',
      });
      await actions.login('user', 'password');
      expect(useAuthStore.getState().isAuthenticated).toBe(true);

      // Mock token as not expiring soon
      (tokenUtils.isTokenExpiringSoon as Mock).mockReturnValue(false);

      // Check token expiration
      actions.checkTokenExpiration();

      // Should remain logged in with original tokens
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.user).toEqual({ username: 'user', password: '' });
      expect(newState.token).toBe('test-token');
      expect(newState.refreshToken).toBe('test-refresh-token');
      expect(api.refreshToken).not.toHaveBeenCalled();
    });

    it('should handle null token gracefully', () => {
      const { actions } = store;

      // Ensure no token is set
      expect(useAuthStore.getState().token).toBeNull();

      // Mock isTokenExpiringSoon to return true for null
      (tokenUtils.isTokenExpiringSoon as Mock).mockReturnValue(true);

      // Check token expiration
      actions.checkTokenExpiration();

      // Should call logout but state is already logged out
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.token).toBeNull();
    });
  });

  describe('Token Rehydration (via checkTokenExpiration)', () => {
    it('should refresh tokens on rehydration when token is expiring', async () => {
      // Mock isTokenExpiringSoon to return true (token is expiring)
      (tokenUtils.isTokenExpiringSoon as Mock).mockReturnValue(true);

      // Mock successful token refresh
      (api.refreshToken as Mock).mockResolvedValue({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
      });

      // Set up authenticated state with an expiring token
      const testState = {
        isAuthenticated: true,
        user: { username: 'testuser', password: '' },
        token: 'expiring-token',
        refreshToken: 'valid-refresh-token',
        error: null,
        actions: useAuthStore.getState().actions,
      };

      act(() => {
        useAuthStore.setState(testState);
      });

      // Simulate the onRehydrateStorage callback by manually calling the logic
      // This is what Zustand persist does after rehydrating from localStorage
      const state = useAuthStore.getState();
      if (state?.token && tokenUtils.isTokenExpiringSoon(state.token)) {
        await act(async () => {
          await state.actions.refreshTokens();
        });
      }

      // Verify that tokens were refreshed
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.token).toBe('new-access-token');
      expect(newState.refreshToken).toBe('new-refresh-token');
      expect(api.refreshToken).toHaveBeenCalledWith('valid-refresh-token');
    });

    it('should refresh when checking an expiring token', async () => {
      // Mock isTokenExpiringSoon to return true
      (tokenUtils.isTokenExpiringSoon as Mock).mockReturnValue(true);

      // Mock successful token refresh
      (api.refreshToken as Mock).mockResolvedValue({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
      });

      // Set up authenticated state with a token
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          user: { username: 'testuser', password: '' },
          token: 'expiring-token',
          refreshToken: 'valid-refresh-token',
          error: null,
        });
      });

      // Manually trigger the token expiration check (simulates rehydration)
      await act(async () => {
        useAuthStore.getState().actions.checkTokenExpiration();
        await new Promise((resolve) => setTimeout(resolve, 0));
      });

      // Verify that tokens were refreshed
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.token).toBe('new-access-token');
      expect(newState.refreshToken).toBe('new-refresh-token');
    });

    it('should not refresh when checking a valid token', () => {
      // Mock isTokenExpiringSoon to return false
      (tokenUtils.isTokenExpiringSoon as Mock).mockReturnValue(false);

      // Set up authenticated state with a valid token
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          user: { username: 'testuser', password: '' },
          token: 'valid-token',
          refreshToken: 'valid-refresh-token',
          error: null,
        });
      });

      // Manually trigger the token expiration check
      act(() => {
        useAuthStore.getState().actions.checkTokenExpiration();
      });

      // Verify that state remains unchanged
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.token).toBe('valid-token');
      expect(newState.refreshToken).toBe('valid-refresh-token');
      expect(newState.user).toEqual({ username: 'testuser', password: '' });
      expect(api.refreshToken).not.toHaveBeenCalled();
    });

    it('should handle null token when checking expiration', () => {
      // Mock isTokenExpiringSoon to return false for null
      (tokenUtils.isTokenExpiringSoon as Mock).mockReturnValue(false);

      // Set up state with no token
      act(() => {
        useAuthStore.setState({
          isAuthenticated: false,
          user: null,
          token: null,
          error: null,
        });
      });

      // Check expiration should not throw
      expect(() => {
        act(() => {
          useAuthStore.getState().actions.checkTokenExpiration();
        });
      }).not.toThrow();

      // Verify that isTokenExpiringSoon was still called with null
      expect(tokenUtils.isTokenExpiringSoon).toHaveBeenCalledWith(null);
    });
  });
});
