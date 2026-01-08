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

export type TokenSource = 'local' | 'oidc';

export type AuthState = {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  tokenSource: TokenSource;
  error: string | null;
  _refreshPromise: Promise<boolean> | null;
  actions: {
    login: (username: string, password: string) => Promise<boolean>;
    loginWithOIDC: () => Promise<void>;
    handleOIDCCallbackFlow: () => Promise<boolean>;
    logout: () => void;
    clearError: () => void;
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
      _refreshPromise: null,
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
                state.user = { username: oidcUser.profile?.preferred_username || oidcUser.profile?.email || 'OIDC User', password: '' };
                state.error = null;
              });
              return true;
            }
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
          const currentState = useAuthStore.getState();
          if (currentState._refreshPromise) {
            return currentState._refreshPromise;
          }

          // Create refresh promise
          const refreshPromise = (async () => {
            try {
              const state = useAuthStore.getState();

              // Handle OIDC token refresh
              if (state.tokenSource === 'oidc') {
                const oidcUser = await renewOIDCToken();
                if (oidcUser?.access_token) {
                  set((s) => {
                    s.token = oidcUser.access_token;
                    s.refreshToken = oidcUser.refresh_token || null;
                    s.error = null;
                  });
                  return true;
                }
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
              set((s) => {
                s._refreshPromise = null;
              });
            }
          })();

          // Store the in-flight promise to deduplicate concurrent calls
          set((s) => {
            s._refreshPromise = refreshPromise;
          });

          return refreshPromise;
        },

        logout: async () => {
          const state = useAuthStore.getState();

          // Logout from OIDC if applicable
          if (state.tokenSource === 'oidc') {
            try {
              await logoutOIDC();
            } catch (error) {
              // Log OIDC logout errors but continue with local logout
              // OIDC provider may be temporarily unavailable, but we should still clear local auth state
              const errorDetails = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
              console.warn(`OIDC logout failed but continuing with local logout: ${errorDetails}`, { original: error });
            }
          }

          set((state) => {
            state.isAuthenticated = false;
            state.user = null;
            state.token = null;
            state.refreshToken = null;
            state.error = null;
            state._refreshPromise = null;
          });
        },

        clearError: () => {
          set((state) => {
            state.error = null;
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
