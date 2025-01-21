import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { User } from '../../../types';
import * as api from '../../../services/api';

export type AuthState = {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  error: string | null;
  actions: {
    login: (username: string, password: string) => Promise<boolean>;
    logout: () => void;
    clearError: () => void;
  };
};

export const useAuthStore = create<AuthState>()(
  persist(
    immer((set) => ({
      isAuthenticated: false,
      user: null,
      token: null,
      error: null,
      actions: {
        login: async (username, password) => {
          try {
            const response = await api.login(username, password);
            set((state) => {
              state.isAuthenticated = true;
              state.user = { username, password: '' }; // Don't store actual password
              state.token = response.access_token;
              state.error = null;
            });
            return true;
          } catch (error: unknown) {
            const errorMessage =
              error instanceof Error ? error.message : 'Login failed';
            set((state) => {
              state.error = errorMessage;
              state.isAuthenticated = false;
              state.user = null;
              state.token = null;
            });
            return false;
          }
        },

        logout: () => {
          set((state) => {
            state.isAuthenticated = false;
            state.user = null;
            state.token = null;
            state.error = null;
          });
        },

        clearError: () => {
          set((state) => {
            state.error = null;
          });
        },
      },
    })),
    {
      name: 'parchmark-auth',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token,
      }),
      merge: (persistedState, currentState) => {
        return {
          ...currentState,
          ...persistedState,
          error: null, // Don't persist errors
        };
      },
    }
  )
);
