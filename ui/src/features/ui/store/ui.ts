import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { STORAGE_KEYS } from '../../../config/storage';

export type UIState = {
  isSidebarOpen: boolean;
  isDarkMode: boolean;
  actions: {
    toggleSidebar: () => void;
    toggleDarkMode: () => void;
  };
};

// Create stable references for action functions
const createActions = (set: (fn: (state: UIState) => void) => void) => {
  // Define actions outside the store to maintain stable references
  const toggleSidebar = () => {
    set((state: UIState) => {
      state.isSidebarOpen = !state.isSidebarOpen;
    });
  };

  const toggleDarkMode = () => {
    set((state: UIState) => {
      state.isDarkMode = !state.isDarkMode;
    });
  };

  return {
    toggleSidebar,
    toggleDarkMode,
  };
};

export const useUIStore = create<UIState>()(
  persist(
    immer((set) => {
      // Create stable action references
      const actions = createActions(set);

      return {
        isSidebarOpen: true,
        isDarkMode: false,
        actions,
      };
    }),
    {
      name: STORAGE_KEYS.UI_PREFERENCES,
      // Ensure actions are preserved during hydration
      merge: (persistedState, currentState) => {
        return {
          ...persistedState,
          actions: currentState.actions,
        };
      },
    }
  )
);
