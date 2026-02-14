import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { User } from '../../../types';
import * as api from '../../../services/api';
import { isTokenExpiringSoon } from '../utils/tokenUtils';
import { handleError } from '../../../utils/errorHandler';
import { STORAGE_KEYS } from '../../../config/storage';
import {
  startOIDCLogin,
  handleOIDCCallback,
  logoutOIDC,
  renewOIDCToken,
} from '../utils/oidcUtils';

// Module-level variable for synchronous promise deduplication
// Using module scope prevents race conditions that could occur with Zustand state
let _activeRefreshPromise: Promise<boolean> | null = null;

/**
 * Reset the module-level refresh promise state.
 * Used by tests to ensure clean state between test cases.
 * @internal - Only exported for testing purposes
 */
export const _resetRefreshPromise = () => {
  _activeRefreshPromise = null;
};

export type TokenSource = 'local' | 'oidc';

export type AuthState = {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  tokenSource: TokenSource;
  error: string | null;
  oidcLogoutWarning: string | null; // Warning shown when OIDC logout fails
  actions: {
    login: (username: string, password: string) => Promise<boolean>;
    loginWithOIDC: () => Promise<void>;
    handleOIDCCallbackFlow: () => Promise<boolean>;
    logout: () => Promise<void>;
    clearError: () => void;
    clearOidcLogoutWarning: () => void;
    checkTokenExpiration: () => void;
    refreshTokens: () => Promise<boolean>;
  };
};

export const useAuthStore = create<AuthState>()(
  persist(
    immer((set) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      refreshToken: null,
      tokenSource: 'local' as TokenSource,
      error: null,
      oidcLogoutWarning: null,
      actions: {
        login: async (username, password) => {
          try {
            const response = await api.login(username, password);
            set((state) => {
              state.isAuthenticated = true;
              state.user = { username, password: '' }; // Don't store actual password
              state.token = response.access_token;
              state.refreshToken = response.refresh_token;
              state.tokenSource = 'local';
              state.error = null;
              state.oidcLogoutWarning = null; // Clear any previous OIDC logout warning
            });
            return true;
          } catch (error: unknown) {
            const appError = handleError(error);
            set((state) => {
              state.error = appError.message;
              state.isAuthenticated = false;
              state.user = null;
              state.token = null;
              state.refreshToken = null;
            });
            return false;
          }
        },

        loginWithOIDC: async () => {
          try {
            await startOIDCLogin();
          } catch (error: unknown) {
            const appError = handleError(error);
            set((state) => {
              state.error = appError.message;
            });
            throw error;
          }
        },

        handleOIDCCallbackFlow: async () => {
          try {
            const oidcUser = await handleOIDCCallback();
            if (oidcUser?.access_token) {
              set((state) => {
                state.isAuthenticated = true;
                state.token = oidcUser.access_token;
                state.refreshToken = oidcUser.refresh_token || null;
                state.tokenSource = 'oidc';
                state.user = {
                  username:
                    oidcUser.profile?.preferred_username ||
                    oidcUser.profile?.email ||
                    'OIDC User',
                  password: '',
                };
                state.error = null;
                state.oidcLogoutWarning = null; // Clear any previous OIDC logout warning
              });
              return true;
            }
            // OIDC callback returned but without access_token - this is an incomplete response
            const errorMessage = oidcUser
              ? 'Authentication response incomplete. Please try again.'
              : 'Authentication failed. Please try again.';
            console.error(
              `OIDC callback incomplete: ${oidcUser ? 'missing access_token' : 'no user returned'}`
            );
            set((state) => {
              state.error = errorMessage;
              state.isAuthenticated = false;
              state.user = null;
              state.token = null;
              state.refreshToken = null;
            });
            return false;
          } catch (error: unknown) {
            const appError = handleError(error);
            set((state) => {
              state.error = appError.message;
              state.isAuthenticated = false;
              state.user = null;
              state.token = null;
              state.refreshToken = null;
            });
            return false;
          }
        },

        refreshTokens: async () => {
          // Check if a refresh is already in flight to prevent concurrent calls
          // Using module-level variable ensures synchronous check without race conditions
          if (_activeRefreshPromise) {
            return _activeRefreshPromise;
          }

          // Create and immediately store promise for synchronous deduplication
          const refreshPromise = (async () => {
            try {
              const state = useAuthStore.getState();

              // Handle OIDC token refresh
              if (state.tokenSource === 'oidc') {
                const result = await renewOIDCToken();
                if (result.success && result.data?.access_token) {
                  // Extract to local variable to avoid non-null assertions
                  const tokenData = result.data;
                  set((s) => {
                    s.token = tokenData.access_token;
                    s.refreshToken = tokenData.refresh_token || null;
                    s.error = null;
                  });
                  return true;
                }
                // OIDC token refresh failed - log out user with error message
                const errorDetail = !result.success
                  ? `renewal failed: ${result.error?.message || 'unknown error'}`
                  : 'renewal returned no access token';
                console.error(`OIDC token refresh failed: ${errorDetail}`);
                set((s) => {
                  s.error = 'Session expired. Please sign in again.';
                  s.isAuthenticated = false;
                  s.user = null;
                  s.token = null;
                  s.refreshToken = null;
                });
                return false;
              }

              // Handle local token refresh
              if (!state.refreshToken) {
                return false;
              }

              const response = await api.refreshToken(state.refreshToken);
              set((s) => {
                s.token = response.access_token;
                s.refreshToken = response.refresh_token;
                s.error = null;
              });
              return true;
            } catch (error: unknown) {
              const appError = handleError(error);
              set((s) => {
                s.error = appError.message;
                s.isAuthenticated = false;
                s.user = null;
                s.token = null;
                s.refreshToken = null;
              });
              return false;
            } finally {
              // Clear the in-flight promise when refresh completes
              _activeRefreshPromise = null;
            }
          })();

          // Store immediately for synchronous deduplication
          _activeRefreshPromise = refreshPromise;

          return refreshPromise;
        },

        logout: async () => {
          const state = useAuthStore.getState();
          const wasOIDC = state.tokenSource === 'oidc';

          _activeRefreshPromise = null;

          if (wasOIDC) {
            // Clear persisted state so the user returns unauthenticated
            // after the OIDC provider redirects back. Avoid updating React
            // state here — that triggers a Router redirect to /login which
            // races with signoutRedirect's page navigation and breaks
            // dynamic chunk imports.
            localStorage.removeItem(STORAGE_KEYS.AUTH);
            // Don't await — signoutRedirect navigates the page away and its
            // promise never resolves (the page unloads). Awaiting it would
            // keep the JS event loop alive during page teardown, allowing
            // aborted in-flight fetches to propagate as NetworkErrors to
            // React Router error boundaries. If the redirect fails, the
            // catch handler falls back to local cleanup.
            return logoutOIDC().catch((error) => {
              const errorDetails =
                error instanceof Error
                  ? `${error.name}: ${error.message}`
                  : String(error);
              console.warn(
                `OIDC logout failed but continuing with local logout: ${errorDetails}`,
                { original: error }
              );
              set((state) => {
                state.isAuthenticated = false;
                state.user = null;
                state.token = null;
                state.refreshToken = null;
                state.error = null;
                state.oidcLogoutWarning =
                  'Your session may still be active on the identity provider. For complete logout, close your browser or visit the identity provider directly.';
              });
            });
          } else {
            set((state) => {
              state.isAuthenticated = false;
              state.user = null;
              state.token = null;
              state.refreshToken = null;
              state.error = null;
              state.oidcLogoutWarning = null;
            });
          }
        },

        clearError: () => {
          set((state) => {
            state.error = null;
          });
        },

        clearOidcLogoutWarning: () => {
          set((state) => {
            state.oidcLogoutWarning = null;
          });
        },

        checkTokenExpiration: () => {
          const state = useAuthStore.getState();
          if (isTokenExpiringSoon(state.token)) {
            // Try to refresh tokens instead of logging out
            state.actions.refreshTokens();
          }
        },
      },
    })),
    {
      name: STORAGE_KEYS.AUTH,
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        tokenSource: state.tokenSource,
        // Note: _refreshPromise is intentionally excluded (never persisted to localStorage)
      }),
      onRehydrateStorage: () => (state) => {
        // Check token expiration after rehydration
        if (state?.token && isTokenExpiringSoon(state.token)) {
          // Try to refresh tokens instead of logging out
          state.actions.refreshTokens();
        }
      },
    }
  )
);
