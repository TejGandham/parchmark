import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { STORAGE_KEYS } from '../../../config/storage';
import { SortOption, SortDirection } from '../../../utils/dateGrouping';

export type UIState = {
  isSidebarOpen: boolean;
  notesSortBy: SortOption;
  notesSortDirection: SortDirection;
  notesSearchQuery: string;
  notesGroupByDate: boolean;
  actions: {
    toggleSidebar: () => void;
    setNotesSortBy: (sortBy: SortOption) => void;
    toggleNotesSortDirection: () => void;
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

  const setNotesSortBy = (sortBy: SortOption) => {
    set((state: UIState) => {
      state.notesSortBy = sortBy;
    });
  };

  const toggleNotesSortDirection = () => {
    set((state: UIState) => {
      state.notesSortDirection =
        state.notesSortDirection === 'desc' ? 'asc' : 'desc';
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
    setNotesSortBy,
    toggleNotesSortDirection,
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
        notesSortBy: 'lastModified' as SortOption,
        notesSortDirection: 'desc' as SortDirection,
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
