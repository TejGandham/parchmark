import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { act } from 'react';
import {
  useAuthStore,
  _resetRefreshPromise,
} from '../../../../features/auth/store/auth';
import * as oidcUtils from '../../../../features/auth/utils/oidcUtils';

vi.mock('../../../../features/auth/utils/oidcUtils', () => ({
  startOIDCLogin: vi.fn(),
  handleOIDCCallback: vi.fn(),
  logoutOIDC: vi.fn(),
  renewOIDCToken: vi.fn().mockResolvedValue({ success: true, data: null }),
}));

vi.mock('../../../../services/api', () => ({
  login: vi.fn(),
  refreshToken: vi.fn(),
}));

describe('Auth Store - OIDC Methods', () => {
  beforeEach(() => {
    // Reset module-level state for token refresh deduplication
    _resetRefreshPromise();

    // Reset the store before each test using setState (avoids localStorage persist issues)
    act(() => {
      useAuthStore.setState({
        isAuthenticated: false,
        user: null,
        token: null,
        refreshToken: null,
        tokenSource: 'local',
        error: null,
        oidcLogoutWarning: null,
        actions: useAuthStore.getState().actions,
      });
    });
    vi.clearAllMocks();
  });

  describe('initialization', () => {
    it('initializes with local token source', () => {
      const store = useAuthStore.getState();
      expect(store.tokenSource).toBe('local');
      expect(store.oidcLogoutWarning).toBeNull();
    });
  });

  describe('handleOIDCCallbackFlow', () => {
    it('sets OIDC token source and user on successful callback', async () => {
      const mockUser = {
        access_token: 'oidc-access-token',
        refresh_token: 'oidc-refresh-token',
        profile: {
          preferred_username: 'oidcuser',
          email: 'oidc@example.com',
        },
      };
      (oidcUtils.handleOIDCCallback as Mock).mockResolvedValue(mockUser);

      const store = useAuthStore.getState();
      const result = await store.actions.handleOIDCCallbackFlow();

      const newState = useAuthStore.getState();
      expect(result).toBe(true);
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.token).toBe('oidc-access-token');
      expect(newState.refreshToken).toBe('oidc-refresh-token');
      expect(newState.tokenSource).toBe('oidc');
      expect(newState.user).toEqual({ username: 'oidcuser', password: '' });
      expect(newState.error).toBeNull();
    });

    it('uses email as fallback username when preferred_username is missing', async () => {
      const mockUser = {
        access_token: 'oidc-token',
        profile: {
          email: 'fallback@example.com',
        },
      };
      (oidcUtils.handleOIDCCallback as Mock).mockResolvedValue(mockUser);

      const store = useAuthStore.getState();
      await store.actions.handleOIDCCallbackFlow();

      const newState = useAuthStore.getState();
      expect(newState.user?.username).toBe('fallback@example.com');
    });

    it('uses "OIDC User" when no username or email available', async () => {
      const mockUser = {
        access_token: 'oidc-token',
        profile: {},
      };
      (oidcUtils.handleOIDCCallback as Mock).mockResolvedValue(mockUser);

      const store = useAuthStore.getState();
      await store.actions.handleOIDCCallbackFlow();

      const newState = useAuthStore.getState();
      expect(newState.user?.username).toBe('OIDC User');
    });

    it('sets error when callback returns user without access_token', async () => {
      const mockUser = {
        profile: { preferred_username: 'notoken' },
      };
      (oidcUtils.handleOIDCCallback as Mock).mockResolvedValue(mockUser);

      const store = useAuthStore.getState();
      const result = await store.actions.handleOIDCCallbackFlow();

      const newState = useAuthStore.getState();
      expect(result).toBe(false);
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.error).toBe(
        'Authentication response incomplete. Please try again.'
      );
      expect(newState.token).toBeNull();
    });

    it('sets error when callback returns null', async () => {
      (oidcUtils.handleOIDCCallback as Mock).mockResolvedValue(null);

      const store = useAuthStore.getState();
      const result = await store.actions.handleOIDCCallbackFlow();

      const newState = useAuthStore.getState();
      expect(result).toBe(false);
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.error).toBe('Authentication failed. Please try again.');
    });

    it('handles callback exceptions properly', async () => {
      (oidcUtils.handleOIDCCallback as Mock).mockRejectedValue(
        new Error('OIDC provider unavailable')
      );

      const store = useAuthStore.getState();
      const result = await store.actions.handleOIDCCallbackFlow();

      const newState = useAuthStore.getState();
      expect(result).toBe(false);
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.error).toBe('OIDC provider unavailable');
    });

    it('clears oidcLogoutWarning on successful OIDC login', async () => {
      // Set up a previous logout warning
      act(() => {
        useAuthStore.setState({ oidcLogoutWarning: 'Previous warning' });
      });

      const mockUser = {
        access_token: 'token',
        profile: { preferred_username: 'user' },
      };
      (oidcUtils.handleOIDCCallback as Mock).mockResolvedValue(mockUser);

      const store = useAuthStore.getState();
      await store.actions.handleOIDCCallbackFlow();

      const newState = useAuthStore.getState();
      expect(newState.oidcLogoutWarning).toBeNull();
    });
  });

  describe('OIDC token refresh (refreshTokens)', () => {
    it('refreshes OIDC token successfully', async () => {
      // Set up OIDC authenticated state
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          token: 'old-oidc-token',
          refreshToken: 'old-refresh-token',
          tokenSource: 'oidc',
          user: { username: 'oidcuser', password: '' },
        });
      });

      const newUser = {
        access_token: 'new-oidc-token',
        refresh_token: 'new-refresh-token',
      };
      (oidcUtils.renewOIDCToken as Mock).mockResolvedValue({
        success: true,
        data: newUser,
      });

      const store = useAuthStore.getState();
      const result = await store.actions.refreshTokens();

      const newState = useAuthStore.getState();
      expect(result).toBe(true);
      expect(newState.token).toBe('new-oidc-token');
      expect(newState.refreshToken).toBe('new-refresh-token');
      expect(newState.isAuthenticated).toBe(true);
      expect(newState.error).toBeNull();
    });

    it('logs out user when OIDC renewal fails with error', async () => {
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          token: 'oidc-token',
          tokenSource: 'oidc',
          user: { username: 'oidcuser', password: '' },
        });
      });

      (oidcUtils.renewOIDCToken as Mock).mockResolvedValue({
        success: false,
        error: new Error('Session expired on IDP'),
      });

      const store = useAuthStore.getState();
      const result = await store.actions.refreshTokens();

      const newState = useAuthStore.getState();
      expect(result).toBe(false);
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.token).toBeNull();
      expect(newState.user).toBeNull();
      expect(newState.error).toBe('Session expired. Please sign in again.');
    });

    it('logs out user when OIDC renewal returns no access_token', async () => {
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          token: 'oidc-token',
          tokenSource: 'oidc',
          user: { username: 'oidcuser', password: '' },
        });
      });

      (oidcUtils.renewOIDCToken as Mock).mockResolvedValue({
        success: true,
        data: { profile: {} }, // Missing access_token
      });

      const store = useAuthStore.getState();
      const result = await store.actions.refreshTokens();

      const newState = useAuthStore.getState();
      expect(result).toBe(false);
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.error).toBe('Session expired. Please sign in again.');
    });

    it('logs out user when OIDC renewal returns null data', async () => {
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          token: 'oidc-token',
          tokenSource: 'oidc',
          user: { username: 'oidcuser', password: '' },
        });
      });

      (oidcUtils.renewOIDCToken as Mock).mockResolvedValue({
        success: true,
        data: null,
      });

      const store = useAuthStore.getState();
      const result = await store.actions.refreshTokens();

      const newState = useAuthStore.getState();
      expect(result).toBe(false);
      expect(newState.isAuthenticated).toBe(false);
    });
  });

  describe('OIDC logout', () => {
    it('clears persisted state and calls signoutRedirect on successful OIDC logout', async () => {
      const removeItemSpy = vi.spyOn(localStorage, 'removeItem');

      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          token: 'oidc-token',
          refreshToken: 'refresh-token',
          tokenSource: 'oidc',
          user: { username: 'oidcuser', password: '' },
        });
      });

      (oidcUtils.logoutOIDC as Mock).mockResolvedValue(undefined);

      const store = useAuthStore.getState();
      await store.actions.logout();

      expect(oidcUtils.logoutOIDC).toHaveBeenCalledTimes(1);
      expect(removeItemSpy).toHaveBeenCalledWith('parchmark-auth');

      removeItemSpy.mockRestore();
    });

    it('sets oidcLogoutWarning when logoutOIDC rejects unexpectedly', async () => {
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          token: 'oidc-token',
          tokenSource: 'oidc',
          user: { username: 'oidcuser', password: '' },
        });
      });

      (oidcUtils.logoutOIDC as Mock).mockRejectedValue(
        new Error('IDP unavailable')
      );

      const store = useAuthStore.getState();
      await store.actions.logout();

      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(false);
      expect(newState.token).toBeNull();
      expect(newState.oidcLogoutWarning).toContain(
        'session may still be active'
      );
    });

    it('does not set oidcLogoutWarning when logoutOIDC resolves (native fallback redirect)', async () => {
      const removeItemSpy = vi.spyOn(localStorage, 'removeItem');

      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          token: 'oidc-token',
          tokenSource: 'oidc',
          user: { username: 'oidcuser', password: '' },
        });
      });

      (oidcUtils.logoutOIDC as Mock).mockReturnValue(
        new Promise<never>(() => {})
      );

      const store = useAuthStore.getState();
      store.actions.logout();

      await new Promise((r) => setTimeout(r, 50));

      const newState = useAuthStore.getState();
      expect(removeItemSpy).toHaveBeenCalledWith('parchmark-auth');
      expect(newState.oidcLogoutWarning).toBeNull();

      removeItemSpy.mockRestore();
    });

    it('does not call logoutOIDC for local token source', async () => {
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          token: 'local-token',
          tokenSource: 'local',
          user: { username: 'localuser', password: '' },
        });
      });

      const store = useAuthStore.getState();
      await store.actions.logout();

      expect(oidcUtils.logoutOIDC).not.toHaveBeenCalled();
      const newState = useAuthStore.getState();
      expect(newState.isAuthenticated).toBe(false);
    });
  });

  describe('oidcLogoutWarning management', () => {
    it('clearOidcLogoutWarning clears the warning', () => {
      act(() => {
        useAuthStore.setState({
          oidcLogoutWarning: 'Your session may still be active',
        });
      });

      const store = useAuthStore.getState();
      act(() => {
        store.actions.clearOidcLogoutWarning();
      });

      const newState = useAuthStore.getState();
      expect(newState.oidcLogoutWarning).toBeNull();
    });

    it('oidcLogoutWarning is cleared on new local login', async () => {
      const api = await import('../../../../services/api');
      (api.login as Mock).mockResolvedValue({
        access_token: 'local-token',
        refresh_token: 'local-refresh',
      });

      act(() => {
        useAuthStore.setState({
          oidcLogoutWarning: 'Previous OIDC session warning',
        });
      });

      const store = useAuthStore.getState();
      await store.actions.login('user', 'password');

      const newState = useAuthStore.getState();
      expect(newState.oidcLogoutWarning).toBeNull();
      expect(newState.tokenSource).toBe('local');
    });
  });

  describe('token source persistence', () => {
    it('persists tokenSource in localStorage', async () => {
      const mockUser = {
        access_token: 'oidc-token',
        profile: { preferred_username: 'user' },
      };
      (oidcUtils.handleOIDCCallback as Mock).mockResolvedValue(mockUser);

      const store = useAuthStore.getState();
      await store.actions.handleOIDCCallbackFlow();

      // tokenSource should be in state
      expect(useAuthStore.getState().tokenSource).toBe('oidc');
    });

    it('clears localStorage on successful OIDC logout for clean rehydration', async () => {
      const removeItemSpy = vi.spyOn(localStorage, 'removeItem');

      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          tokenSource: 'oidc',
          token: 'token',
        });
      });

      (oidcUtils.logoutOIDC as Mock).mockResolvedValue(undefined);

      const store = useAuthStore.getState();
      await store.actions.logout();

      expect(removeItemSpy).toHaveBeenCalledWith('parchmark-auth');
      expect(oidcUtils.logoutOIDC).toHaveBeenCalledTimes(1);

      removeItemSpy.mockRestore();
    });
  });

  describe('loginWithOIDC', () => {
    it('calls startOIDCLogin', async () => {
      (oidcUtils.startOIDCLogin as Mock).mockResolvedValue(undefined);

      const store = useAuthStore.getState();
      await store.actions.loginWithOIDC();

      expect(oidcUtils.startOIDCLogin).toHaveBeenCalledTimes(1);
    });

    it('sets error on OIDC login failure', async () => {
      (oidcUtils.startOIDCLogin as Mock).mockRejectedValue(
        new Error('Configuration error')
      );

      const store = useAuthStore.getState();
      await expect(store.actions.loginWithOIDC()).rejects.toThrow(
        'Configuration error'
      );

      const newState = useAuthStore.getState();
      expect(newState.error).toBe('Configuration error');
    });
  });
});
