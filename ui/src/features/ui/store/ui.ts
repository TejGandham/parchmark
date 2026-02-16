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
  isPaletteOpen: boolean;
  paletteSearchQuery: string;
  actions: {
    toggleSidebar: () => void;
    setNotesSortBy: (sortBy: SortOption) => void;
    toggleNotesSortDirection: () => void;
    setNotesSearchQuery: (query: string) => void;
    setNotesGroupByDate: (enabled: boolean) => void;
    openPalette: () => void;
    closePalette: () => void;
    togglePalette: () => void;
    setPaletteSearchQuery: (query: string) => void;
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

  const openPalette = () => {
    set((state: UIState) => {
      state.isPaletteOpen = true;
    });
  };

  const closePalette = () => {
    set((state: UIState) => {
      state.isPaletteOpen = false;
      state.paletteSearchQuery = '';
    });
  };

  const togglePalette = () => {
    set((state: UIState) => {
      state.isPaletteOpen = !state.isPaletteOpen;
      if (!state.isPaletteOpen) {
        state.paletteSearchQuery = '';
      }
    });
  };

  const setPaletteSearchQuery = (query: string) => {
    set((state: UIState) => {
      state.paletteSearchQuery = query;
    });
  };

  return {
    toggleSidebar,
    setNotesSortBy,
    toggleNotesSortDirection,
    setNotesSearchQuery,
    setNotesGroupByDate,
    openPalette,
    closePalette,
    togglePalette,
    setPaletteSearchQuery,
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
        isPaletteOpen: false,
        paletteSearchQuery: '',
        actions,
      };
    }),
    {
      name: STORAGE_KEYS.UI_PREFERENCES,
      version: 2,
      migrate: (
        persistedState: unknown,
        version: number
      ): UIState | Promise<UIState> => {
        const state = persistedState as Partial<UIState>;
        if (version === 0 || version === 1) {
          return {
            ...state,
            isPaletteOpen: false,
            paletteSearchQuery: '',
          } as UIState;
        }
        return state as UIState;
      },
      // Ensure actions are preserved during hydration
      merge: (persistedState, currentState) => {
        return {
          ...persistedState,
          actions: currentState.actions,
        };
      },
      // Exclude ephemeral palette state from persistence
      partialize: (state) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { isPaletteOpen, paletteSearchQuery, actions, ...persisted } =
          state;
        return persisted as UIState;
      },
    }
  )
);
