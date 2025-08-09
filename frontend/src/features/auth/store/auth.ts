import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { User } from '../../../types';

export type AuthState = {
  isAuthenticated: boolean;
  user: User | null;
  error: string | null;
  actions: {
    login: (username: string, password: string) => boolean;
    logout: () => void;
    clearError: () => void;
  };
};

// Demo credentials for testing
const DEMO_USER = {
  username: 'user',
  password: 'password',
};

export const useAuthStore = create<AuthState>()(
  persist(
    immer((set) => ({
      isAuthenticated: false,
      user: null,
      error: null,
      actions: {
        login: (username: string, password: string) => {
          // Simple validation - in a real app this would call an API
          if (
            username === DEMO_USER.username &&
            password === DEMO_USER.password
          ) {
            set((state) => {
              state.isAuthenticated = true;
              state.user = { username, password: '' }; // Don't store actual password
              state.error = null;
            });
            return true;
          } else {
            set((state) => {
              state.error = 'Invalid username or password';
              state.isAuthenticated = false;
              state.user = null;
            });
            return false;
          }
        },

        logout: () => {
          set((state) => {
            state.isAuthenticated = false;
            state.user = null;
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
        user: state.user
          ? { username: state.user.username, password: '' }
          : null,
      }),
      merge: (persistedState, currentState) => {
        return {
          ...persistedState,
          error: null,
          actions: currentState.actions,
        };
      },
    }
  )
);
