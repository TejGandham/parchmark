import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Create mock functions at module scope - vi.hoisted ensures they're available to vi.mock
const mockFns = vi.hoisted(() => ({
  signinRedirect: vi.fn(),
  signinRedirectCallback: vi.fn(),
  getUser: vi.fn(),
  signinSilent: vi.fn(),
  signoutRedirect: vi.fn(),
  removeUser: vi.fn(),
}));

// Mock oidc-client-ts before any imports
vi.mock('oidc-client-ts', () => ({
  UserManager: vi.fn(() => ({
    signinRedirect: mockFns.signinRedirect,
    signinRedirectCallback: mockFns.signinRedirectCallback,
    getUser: mockFns.getUser,
    signinSilent: mockFns.signinSilent,
    signoutRedirect: mockFns.signoutRedirect,
    removeUser: mockFns.removeUser,
  })),
  WebStorageStateStore: vi.fn(),
}));

// Import functions to test after mock setup
import {
  startOIDCLogin,
  handleOIDCCallback,
  getOIDCUser,
  renewOIDCToken,
  logoutOIDC,
} from '../../../../features/auth/utils/oidcUtils';

describe('OIDC Utils', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('startOIDCLogin', () => {
    it('calls userManager.signinRedirect', async () => {
      mockFns.signinRedirect.mockResolvedValue(undefined);

      await startOIDCLogin();

      expect(mockFns.signinRedirect).toHaveBeenCalledTimes(1);
    });

    it('throws and logs error on failure', async () => {
      const error = new Error('Redirect failed');
      mockFns.signinRedirect.mockRejectedValue(error);

      await expect(startOIDCLogin()).rejects.toThrow('Redirect failed');
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('OIDC login failed'),
        expect.any(Object)
      );
    });
  });

  describe('handleOIDCCallback', () => {
    it('returns user from signinRedirectCallback', async () => {
      const mockUser = {
        access_token: 'access_token_value',
        refresh_token: 'refresh_token_value',
        profile: {
          sub: 'user-123',
          preferred_username: 'testuser',
          email: 'test@example.com',
        },
      };
      mockFns.signinRedirectCallback.mockResolvedValue(mockUser);

      const result = await handleOIDCCallback();

      expect(mockFns.signinRedirectCallback).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockUser);
      expect(result?.access_token).toBe('access_token_value');
      expect(result?.profile?.preferred_username).toBe('testuser');
    });

    it('throws and logs error on failure', async () => {
      const error = new Error('Callback failed');
      mockFns.signinRedirectCallback.mockRejectedValue(error);

      await expect(handleOIDCCallback()).rejects.toThrow('Callback failed');
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('OIDC callback failed'),
        expect.any(Object)
      );
    });
  });

  describe('getOIDCUser', () => {
    it('returns success result with user when logged in', async () => {
      const mockUser = {
        access_token: 'token',
        profile: { sub: 'user-123' },
      };
      mockFns.getUser.mockResolvedValue(mockUser);

      const result = await getOIDCUser();

      expect(mockFns.getUser).toHaveBeenCalledTimes(1);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(mockUser);
      }
    });

    it('returns success result with null when no user', async () => {
      mockFns.getUser.mockResolvedValue(null);

      const result = await getOIDCUser();

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toBeNull();
      }
    });

    it('returns failure result with error on failure', async () => {
      const error = new Error('Storage error');
      mockFns.getUser.mockRejectedValue(error);

      const result = await getOIDCUser();

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.message).toBe('Storage error');
      }
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Failed to get OIDC user'),
        expect.any(Object)
      );
    });
  });

  describe('renewOIDCToken', () => {
    it('returns success result with user on successful silent renewal', async () => {
      const mockUser = {
        access_token: 'new_token',
        refresh_token: 'new_refresh',
        profile: { sub: 'user-123' },
      };
      mockFns.signinSilent.mockResolvedValue(mockUser);

      const result = await renewOIDCToken();

      expect(mockFns.signinSilent).toHaveBeenCalledTimes(1);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(mockUser);
        expect(result.data?.access_token).toBe('new_token');
      }
    });

    it('returns failure result with error on failure', async () => {
      const error = new Error('Silent renewal failed');
      mockFns.signinSilent.mockRejectedValue(error);

      const result = await renewOIDCToken();

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.message).toBe('Silent renewal failed');
      }
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('OIDC token renewal failed'),
        expect.any(Object)
      );
    });
  });

  describe('logoutOIDC', () => {
    it('calls signoutRedirect to end OIDC provider session', async () => {
      mockFns.signoutRedirect.mockResolvedValue(undefined);

      await logoutOIDC();

      expect(mockFns.signoutRedirect).toHaveBeenCalledTimes(1);
      expect(mockFns.removeUser).not.toHaveBeenCalled();
    });

    it('falls back to native provider logout when signoutRedirect fails', async () => {
      const assignSpy = vi
        .spyOn(window.location, 'assign')
        .mockImplementation(() => {});
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      mockFns.signoutRedirect.mockRejectedValue(
        new Error('No end session endpoint')
      );
      mockFns.removeUser.mockResolvedValue(undefined);

      const resultPromise = logoutOIDC();

      await vi.waitFor(() => {
        expect(assignSpy).toHaveBeenCalledTimes(1);
      });

      expect(mockFns.removeUser).toHaveBeenCalledTimes(1);

      const assignedUrl = assignSpy.mock.calls[0][0] as string;
      expect(assignedUrl).toContain('/logout?rd=');
      expect(assignedUrl).toContain(encodeURIComponent('/login'));

      expect(warnSpy).toHaveBeenCalledWith(
        expect.stringContaining('OIDC signoutRedirect unavailable')
      );

      assignSpy.mockRestore();
      warnSpy.mockRestore();

      // Verify the promise stays pending (page navigates away in production).
      let resolved = false;
      resultPromise.then(() => {
        resolved = true;
      });
      await new Promise((r) => setTimeout(r, 50));
      expect(resolved).toBe(false);
    });

    it('redirects to native logout even when removeUser fails', async () => {
      const assignSpy = vi
        .spyOn(window.location, 'assign')
        .mockImplementation(() => {});
      mockFns.signoutRedirect.mockRejectedValue(
        new Error('No end session endpoint')
      );
      mockFns.removeUser.mockRejectedValue(new Error('Storage error'));

      logoutOIDC();

      await vi.waitFor(() => {
        expect(assignSpy).toHaveBeenCalledTimes(1);
      });

      const assignedUrl = assignSpy.mock.calls[0][0] as string;
      expect(assignedUrl).toContain('/logout?rd=');

      assignSpy.mockRestore();
    });
  });
});
