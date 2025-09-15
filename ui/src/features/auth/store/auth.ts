import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { User } from '../../../types';
import * as api from '../../../services/api';
import { getTimeUntilExpiration, isTokenExpired } from '../utils/tokenUtils';

// Global timer reference for token expiration monitoring
let tokenExpirationTimer: NodeJS.Timeout | null = null;

export type AuthState = {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  error: string | null;
  actions: {
    login: (username: string, password: string) => Promise<boolean>;
    logout: () => void;
    clearError: () => void;
    checkTokenExpiration: () => void;
    startTokenExpirationMonitoring: () => void;
    stopTokenExpirationMonitoring: () => void;
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
            
            // Start monitoring token expiration after successful login
            useAuthStore.getState().actions.startTokenExpirationMonitoring();
            
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
          // Stop monitoring token expiration
          useAuthStore.getState().actions.stopTokenExpirationMonitoring();
          
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
        
        checkTokenExpiration: () => {
          const state = useAuthStore.getState();
          const token = state.token;
          
          if (!token) {
            return;
          }
          
          // Check if token is expired or will expire within 30 seconds
          if (isTokenExpired(token, 30)) {
            console.log('Token expired or expiring soon, logging out...');
            state.actions.logout();
          }
        },
        
        startTokenExpirationMonitoring: () => {
          const state = useAuthStore.getState();
          const token = state.token;
          
          if (!token) {
            return;
          }
          
          // Clear any existing timer
          state.actions.stopTokenExpirationMonitoring();
          
          // Calculate time until we should logout (1 minute before actual expiration)
          const timeUntilExpiration = getTimeUntilExpiration(token);
          const timeUntilLogout = Math.max(0, timeUntilExpiration - 60000); // Logout 1 minute before expiration
          
          if (timeUntilLogout > 0) {
            console.log(`Token expiration monitoring started. Will logout in ${Math.floor(timeUntilLogout / 1000)} seconds`);
            
            tokenExpirationTimer = setTimeout(() => {
              console.log('Token expiring soon, logging out proactively...');
              useAuthStore.getState().actions.logout();
            }, timeUntilLogout);
          } else {
            // Token already expired or expiring within 1 minute
            console.log('Token already expired or expiring soon, logging out immediately...');
            state.actions.logout();
          }
        },
        
        stopTokenExpirationMonitoring: () => {
          if (tokenExpirationTimer) {
            clearTimeout(tokenExpirationTimer);
            tokenExpirationTimer = null;
            console.log('Token expiration monitoring stopped');
          }
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
        const merged = {
          ...currentState,
          ...persistedState,
          error: null, // Don't persist errors
        };
        
        // Check token expiration and start monitoring on app initialization
        if (merged.token) {
          // Use setTimeout to avoid calling actions during store initialization
          setTimeout(() => {
            const state = useAuthStore.getState();
            if (isTokenExpired(merged.token, 30)) {
              console.log('Stored token is expired, logging out...');
              state.actions.logout();
            } else {
              // Start monitoring if token is still valid
              state.actions.startTokenExpirationMonitoring();
            }
          }, 0);
        }
        
        return merged;
      },
    }
  )
);
