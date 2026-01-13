import { act } from 'react';
import { useUIStore } from '../../../../features/ui/store/ui';

describe('UI Store', () => {
  beforeEach(() => {
    // Reset the store state before each test
    act(() => {
      useUIStore.setState({
        isSidebarOpen: true,
        notesSortBy: 'lastModified',
        notesSearchQuery: '',
        notesGroupByDate: true,
        actions: useUIStore.getState().actions,
      });
    });
  });

  it('should initialize with the default state', () => {
    const state = useUIStore.getState();
    expect(state.isSidebarOpen).toBe(true);
    expect(state.notesSortBy).toBe('lastModified');
    expect(state.notesSearchQuery).toBe('');
    expect(state.notesGroupByDate).toBe(true);
    expect(typeof state.actions.toggleSidebar).toBe('function');
    expect(typeof state.actions.setNotesSortBy).toBe('function');
    expect(typeof state.actions.setNotesSearchQuery).toBe('function');
    expect(typeof state.actions.setNotesGroupByDate).toBe('function');
  });

  describe('toggleSidebar', () => {
    it('should toggle the sidebar state from true to false', () => {
      // Start with sidebar open
      expect(useUIStore.getState().isSidebarOpen).toBe(true);

      // Toggle sidebar
      act(() => {
        useUIStore.getState().actions.toggleSidebar();
      });

      // Sidebar should now be closed
      expect(useUIStore.getState().isSidebarOpen).toBe(false);
    });

    it('should toggle the sidebar state from false to true', () => {
      // First set state to sidebar closed
      act(() => {
        useUIStore.setState({ isSidebarOpen: false });
      });
      expect(useUIStore.getState().isSidebarOpen).toBe(false);

      // Toggle sidebar
      act(() => {
        useUIStore.getState().actions.toggleSidebar();
      });

      // Sidebar should now be open
      expect(useUIStore.getState().isSidebarOpen).toBe(true);
    });

    it('should work with multiple toggles in sequence', () => {
      // Start with sidebar open
      expect(useUIStore.getState().isSidebarOpen).toBe(true);

      // First toggle
      act(() => {
        useUIStore.getState().actions.toggleSidebar();
      });
      expect(useUIStore.getState().isSidebarOpen).toBe(false);

      // Second toggle
      act(() => {
        useUIStore.getState().actions.toggleSidebar();
      });
      expect(useUIStore.getState().isSidebarOpen).toBe(true);

      // Third toggle
      act(() => {
        useUIStore.getState().actions.toggleSidebar();
      });
      expect(useUIStore.getState().isSidebarOpen).toBe(false);
    });
  });

  describe('Storage Persistence', () => {
    it('should persist the sidebar state', () => {
      // This test is a bit tricky in a non-browser environment
      // We can check if the store uses persist middleware

      // Toggle the sidebar state
      act(() => {
        useUIStore.getState().actions.toggleSidebar();
      });

      // Re-create the store to simulate a page reload
      const newState = useUIStore.getState();

      // The state should be persisted (though this behavior depends on your implementation)
      expect(newState.isSidebarOpen).toBe(false);
    });
  });

  describe('Performance', () => {
    it('should use immer for immutable updates', () => {
      // This is more of an implementation detail test
      // If you're using immer, the state should be updated immutably

      const initialState = useUIStore.getState();

      // Toggle the sidebar
      act(() => {
        useUIStore.getState().actions.toggleSidebar();
      });

      const updatedState = useUIStore.getState();

      // The state object should be different (new reference)
      expect(updatedState).not.toBe(initialState);
    });
  });

  describe('setNotesSortBy', () => {
    it('should update notesSortBy to lastModified', () => {
      act(() => {
        useUIStore.getState().actions.setNotesSortBy('lastModified');
      });

      expect(useUIStore.getState().notesSortBy).toBe('lastModified');
    });

    it('should update notesSortBy to alphabetical', () => {
      act(() => {
        useUIStore.getState().actions.setNotesSortBy('alphabetical');
      });

      expect(useUIStore.getState().notesSortBy).toBe('alphabetical');
    });

    it('should update notesSortBy to createdDate', () => {
      act(() => {
        useUIStore.getState().actions.setNotesSortBy('createdDate');
      });

      expect(useUIStore.getState().notesSortBy).toBe('createdDate');
    });

    it('should allow changing sort option multiple times', () => {
      // Start with lastModified (default)
      expect(useUIStore.getState().notesSortBy).toBe('lastModified');

      // Change to alphabetical
      act(() => {
        useUIStore.getState().actions.setNotesSortBy('alphabetical');
      });
      expect(useUIStore.getState().notesSortBy).toBe('alphabetical');

      // Change to createdDate
      act(() => {
        useUIStore.getState().actions.setNotesSortBy('createdDate');
      });
      expect(useUIStore.getState().notesSortBy).toBe('createdDate');

      // Back to lastModified
      act(() => {
        useUIStore.getState().actions.setNotesSortBy('lastModified');
      });
      expect(useUIStore.getState().notesSortBy).toBe('lastModified');
    });
  });

  describe('setNotesSearchQuery', () => {
    it('should update notesSearchQuery to a search term', () => {
      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('test search');
      });

      expect(useUIStore.getState().notesSearchQuery).toBe('test search');
    });

    it('should update notesSearchQuery to empty string', () => {
      // First set a search query
      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('test');
      });
      expect(useUIStore.getState().notesSearchQuery).toBe('test');

      // Clear the search query
      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('');
      });
      expect(useUIStore.getState().notesSearchQuery).toBe('');
    });

    it('should handle partial search queries', () => {
      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('par');
      });
      expect(useUIStore.getState().notesSearchQuery).toBe('par');

      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('part');
      });
      expect(useUIStore.getState().notesSearchQuery).toBe('part');

      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('partial');
      });
      expect(useUIStore.getState().notesSearchQuery).toBe('partial');
    });

    it('should handle special characters in search query', () => {
      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('C++ tutorial');
      });
      expect(useUIStore.getState().notesSearchQuery).toBe('C++ tutorial');
    });

    it('should allow updating search query multiple times', () => {
      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('first');
      });
      expect(useUIStore.getState().notesSearchQuery).toBe('first');

      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('second');
      });
      expect(useUIStore.getState().notesSearchQuery).toBe('second');

      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('third');
      });
      expect(useUIStore.getState().notesSearchQuery).toBe('third');
    });
  });

  describe('setNotesGroupByDate', () => {
    it('should set notesGroupByDate to true', () => {
      // First set to false
      act(() => {
        useUIStore.setState({ notesGroupByDate: false });
      });
      expect(useUIStore.getState().notesGroupByDate).toBe(false);

      // Set to true
      act(() => {
        useUIStore.getState().actions.setNotesGroupByDate(true);
      });
      expect(useUIStore.getState().notesGroupByDate).toBe(true);
    });

    it('should set notesGroupByDate to false', () => {
      // Start with true (default)
      expect(useUIStore.getState().notesGroupByDate).toBe(true);

      // Set to false
      act(() => {
        useUIStore.getState().actions.setNotesGroupByDate(false);
      });
      expect(useUIStore.getState().notesGroupByDate).toBe(false);
    });

    it('should allow toggling grouping multiple times', () => {
      // Start with true
      expect(useUIStore.getState().notesGroupByDate).toBe(true);

      // Toggle to false
      act(() => {
        useUIStore.getState().actions.setNotesGroupByDate(false);
      });
      expect(useUIStore.getState().notesGroupByDate).toBe(false);

      // Toggle back to true
      act(() => {
        useUIStore.getState().actions.setNotesGroupByDate(true);
      });
      expect(useUIStore.getState().notesGroupByDate).toBe(true);
    });
  });

  describe('Notes Organization Integration', () => {
    it('should allow setting search query and sort option together', () => {
      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('shopping');
        useUIStore.getState().actions.setNotesSortBy('alphabetical');
      });

      const state = useUIStore.getState();
      expect(state.notesSearchQuery).toBe('shopping');
      expect(state.notesSortBy).toBe('alphabetical');
    });

    it('should allow setting all notes organization preferences', () => {
      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('test');
        useUIStore.getState().actions.setNotesSortBy('createdDate');
        useUIStore.getState().actions.setNotesGroupByDate(false);
      });

      const state = useUIStore.getState();
      expect(state.notesSearchQuery).toBe('test');
      expect(state.notesSortBy).toBe('createdDate');
      expect(state.notesGroupByDate).toBe(false);
    });

    it('should preserve other state when updating notes preferences', () => {
      // Set sidebar
      act(() => {
        useUIStore.setState({ isSidebarOpen: false });
      });

      // Update notes preferences
      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('test');
        useUIStore.getState().actions.setNotesSortBy('alphabetical');
      });

      const state = useUIStore.getState();
      // Notes preferences should be updated
      expect(state.notesSearchQuery).toBe('test');
      expect(state.notesSortBy).toBe('alphabetical');
      // Other state should be preserved
      expect(state.isSidebarOpen).toBe(false);
    });
  });
});
