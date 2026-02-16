import { act } from 'react';
import { useUIStore } from '../../../../features/ui/store/ui';

describe('UI Store', () => {
  beforeEach(() => {
    act(() => {
      useUIStore.setState({
        notesSortBy: 'lastModified',
        notesSortDirection: 'desc',
        notesSearchQuery: '',
        notesGroupByDate: true,
        isPaletteOpen: false,
        paletteSearchQuery: '',
        actions: useUIStore.getState().actions,
      });
    });
  });

  it('should initialize with the default state', () => {
    const state = useUIStore.getState();
    expect(state.notesSortBy).toBe('lastModified');
    expect(state.notesSortDirection).toBe('desc');
    expect(state.notesSearchQuery).toBe('');
    expect(state.notesGroupByDate).toBe(true);
    expect(state.isPaletteOpen).toBe(false);
    expect(state.paletteSearchQuery).toBe('');
    expect(typeof state.actions.setNotesSortBy).toBe('function');
    expect(typeof state.actions.toggleNotesSortDirection).toBe('function');
    expect(typeof state.actions.setNotesSearchQuery).toBe('function');
    expect(typeof state.actions.setNotesGroupByDate).toBe('function');
    expect(typeof state.actions.openPalette).toBe('function');
    expect(typeof state.actions.closePalette).toBe('function');
    expect(typeof state.actions.togglePalette).toBe('function');
    expect(typeof state.actions.setPaletteSearchQuery).toBe('function');
  });

  describe('Performance', () => {
    it('should use immer for immutable updates', () => {
      const initialState = useUIStore.getState();

      act(() => {
        useUIStore.getState().actions.setNotesSortBy('alphabetical');
      });

      const updatedState = useUIStore.getState();
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

  describe('toggleNotesSortDirection', () => {
    it('should toggle sort direction from desc to asc', () => {
      expect(useUIStore.getState().notesSortDirection).toBe('desc');

      act(() => {
        useUIStore.getState().actions.toggleNotesSortDirection();
      });

      expect(useUIStore.getState().notesSortDirection).toBe('asc');
    });

    it('should toggle sort direction from asc to desc', () => {
      act(() => {
        useUIStore.setState({ notesSortDirection: 'asc' });
      });
      expect(useUIStore.getState().notesSortDirection).toBe('asc');

      act(() => {
        useUIStore.getState().actions.toggleNotesSortDirection();
      });

      expect(useUIStore.getState().notesSortDirection).toBe('desc');
    });

    it('should work with multiple toggles in sequence', () => {
      expect(useUIStore.getState().notesSortDirection).toBe('desc');

      act(() => {
        useUIStore.getState().actions.toggleNotesSortDirection();
      });
      expect(useUIStore.getState().notesSortDirection).toBe('asc');

      act(() => {
        useUIStore.getState().actions.toggleNotesSortDirection();
      });
      expect(useUIStore.getState().notesSortDirection).toBe('desc');

      act(() => {
        useUIStore.getState().actions.toggleNotesSortDirection();
      });
      expect(useUIStore.getState().notesSortDirection).toBe('asc');
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

  describe('openPalette', () => {
    it('should open the palette', () => {
      expect(useUIStore.getState().isPaletteOpen).toBe(false);

      act(() => {
        useUIStore.getState().actions.openPalette();
      });

      expect(useUIStore.getState().isPaletteOpen).toBe(true);
    });
  });

  describe('closePalette', () => {
    it('should close the palette', () => {
      act(() => {
        useUIStore.setState({ isPaletteOpen: true });
      });

      act(() => {
        useUIStore.getState().actions.closePalette();
      });

      expect(useUIStore.getState().isPaletteOpen).toBe(false);
    });

    it('should clear search query on close', () => {
      act(() => {
        useUIStore.setState({
          isPaletteOpen: true,
          paletteSearchQuery: 'some query',
        });
      });

      act(() => {
        useUIStore.getState().actions.closePalette();
      });

      expect(useUIStore.getState().paletteSearchQuery).toBe('');
    });
  });

  describe('togglePalette', () => {
    it('should toggle palette from closed to open', () => {
      expect(useUIStore.getState().isPaletteOpen).toBe(false);

      act(() => {
        useUIStore.getState().actions.togglePalette();
      });

      expect(useUIStore.getState().isPaletteOpen).toBe(true);
    });

    it('should toggle palette from open to closed and clear query', () => {
      act(() => {
        useUIStore.setState({
          isPaletteOpen: true,
          paletteSearchQuery: 'test',
        });
      });

      act(() => {
        useUIStore.getState().actions.togglePalette();
      });

      expect(useUIStore.getState().isPaletteOpen).toBe(false);
      expect(useUIStore.getState().paletteSearchQuery).toBe('');
    });
  });

  describe('setPaletteSearchQuery', () => {
    it('should update palette search query', () => {
      act(() => {
        useUIStore.getState().actions.setPaletteSearchQuery('hello');
      });

      expect(useUIStore.getState().paletteSearchQuery).toBe('hello');
    });

    it('should clear palette search query', () => {
      act(() => {
        useUIStore.getState().actions.setPaletteSearchQuery('test');
      });

      act(() => {
        useUIStore.getState().actions.setPaletteSearchQuery('');
      });

      expect(useUIStore.getState().paletteSearchQuery).toBe('');
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
        useUIStore.getState().actions.toggleNotesSortDirection();
        useUIStore.getState().actions.setNotesGroupByDate(false);
      });

      const state = useUIStore.getState();
      expect(state.notesSearchQuery).toBe('test');
      expect(state.notesSortBy).toBe('createdDate');
      expect(state.notesSortDirection).toBe('asc');
      expect(state.notesGroupByDate).toBe(false);
    });

    it('should preserve other state when updating notes preferences', () => {
      act(() => {
        useUIStore.getState().actions.openPalette();
      });

      act(() => {
        useUIStore.getState().actions.setNotesSearchQuery('test');
        useUIStore.getState().actions.setNotesSortBy('alphabetical');
      });

      const state = useUIStore.getState();
      expect(state.notesSearchQuery).toBe('test');
      expect(state.notesSortBy).toBe('alphabetical');
      expect(state.isPaletteOpen).toBe(true);
    });
  });
});
