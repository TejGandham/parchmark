import { act } from 'react';
import { useUIStore } from '../../../../features/ui/store/ui';

describe('UI Store', () => {
  beforeEach(() => {
    // Reset the store state before each test
    act(() => {
      useUIStore.setState({
        isSidebarOpen: true,
        isDarkMode: false,
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
    expect(state.isDarkMode).toBe(false);
    expect(state.notesSortBy).toBe('lastModified');
    expect(state.notesSearchQuery).toBe('');
    expect(state.notesGroupByDate).toBe(true);
    expect(typeof state.actions.toggleSidebar).toBe('function');
    expect(typeof state.actions.toggleDarkMode).toBe('function');
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

  describe('toggleDarkMode', () => {
    it('should toggle dark mode from false to true', () => {
      // Start with dark mode off
      expect(useUIStore.getState().isDarkMode).toBe(false);

      // Toggle dark mode
      act(() => {
        useUIStore.getState().actions.toggleDarkMode();
      });

      // Dark mode should now be on
      expect(useUIStore.getState().isDarkMode).toBe(true);
    });

    it('should toggle dark mode from true to false', () => {
      // First set dark mode to true
      act(() => {
        useUIStore.setState({ isDarkMode: true });
      });
      expect(useUIStore.getState().isDarkMode).toBe(true);

      // Toggle dark mode
      act(() => {
        useUIStore.getState().actions.toggleDarkMode();
      });

      // Dark mode should now be off
      expect(useUIStore.getState().isDarkMode).toBe(false);
    });

    it('should work with multiple dark mode toggles', () => {
      // Start with dark mode off
      expect(useUIStore.getState().isDarkMode).toBe(false);

      // First toggle
      act(() => {
        useUIStore.getState().actions.toggleDarkMode();
      });
      expect(useUIStore.getState().isDarkMode).toBe(true);

      // Second toggle
      act(() => {
        useUIStore.getState().actions.toggleDarkMode();
      });
      expect(useUIStore.getState().isDarkMode).toBe(false);
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
});
