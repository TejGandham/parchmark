import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { User } from '../../../types';
import * as api from '../../../services/api';
import { isTokenExpiringSoon } from '../utils/tokenUtils';
import { handleError } from '../../../utils/errorHandler';
import { STORAGE_KEYS } from '../../../config/storage';

export type AuthState = {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  error: string | null;
  actions: {
    login: (username: string, password: string) => Promise<boolean>;
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
      error: null,
      actions: {
        login: async (username, password) => {
          try {
            const response = await api.login(username, password);
            set((state) => {
              state.isAuthenticated = true;
              state.user = { username, password: '' }; // Don't store actual password
              state.token = response.access_token;
              state.refreshToken = response.refresh_token;
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

        refreshTokens: async () => {
          try {
            const state = useAuthStore.getState();
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
          }
        },

        logout: () => {
          set((state) => {
            state.isAuthenticated = false;
            state.user = null;
            state.token = null;
            state.refreshToken = null;
            state.error = null;
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
