import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { STORAGE_KEYS } from '../../../config/storage';
import { SortOption } from '../../../utils/dateGrouping';

export type UIState = {
  isSidebarOpen: boolean;
  isDarkMode: boolean;
  notesSortBy: SortOption;
  notesSearchQuery: string;
  notesGroupByDate: boolean;
  actions: {
    toggleSidebar: () => void;
    toggleDarkMode: () => void;
    setNotesSortBy: (sortBy: SortOption) => void;
    setNotesSearchQuery: (query: string) => void;
    setNotesGroupByDate: (enabled: boolean) => void;
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

  const setNotesSortBy = (sortBy: SortOption) => {
    set((state: UIState) => {
      state.notesSortBy = sortBy;
    });
  };

  const setNotesSearchQuery = (query: string) => {
    set((state: UIState) => {
      state.notesSearchQuery = query;
    });
  };

  const setNotesGroupByDate = (enabled: boolean) => {
    set((state: UIState) => {
      state.notesGroupByDate = enabled;
    });
  };

  return {
    toggleSidebar,
    toggleDarkMode,
    setNotesSortBy,
    setNotesSearchQuery,
    setNotesGroupByDate,
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
        notesSortBy: 'lastModified' as SortOption,
        notesSearchQuery: '',
        notesGroupByDate: true,
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
