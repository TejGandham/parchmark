import { act } from 'react';
import { beforeEach, describe, expect, it, jest } from '@jest/globals';
import {
  useNotesStore,
  NotesState,
} from '../../../../features/notes/store/notes';
import * as api from '../../../../services/api';

jest.mock('../../../../services/api');

// Mock the dependencies
jest.mock('../../../../services/markdownService', () => ({
  extractTitleFromMarkdown: jest.fn().mockImplementation((content) => {
    const match = content.match(/^#\s+(.+)$/m);
    return match ? match[1].trim() : 'Untitled Note';
  }),
  formatNoteContent: jest.fn().mockImplementation((content) => content.trim()),
  createEmptyNoteContent: jest.fn().mockReturnValue('# New Note\n\n'),
}));

// Mock Date.now to return consistent values for testing
const mockDateNow = 1234567890;
jest.spyOn(Date, 'now').mockImplementation(() => mockDateNow);

const mockTimestamp = new Date(mockDateNow).toISOString();
jest.spyOn(Date.prototype, 'toISOString').mockReturnValue(mockTimestamp);

describe('Notes Store', () => {
  let store: NotesState;

  beforeEach(() => {
    // Reset the store before each test
    act(() => {
      useNotesStore.setState({
        notes: [
          {
            id: 'note-1',
            title: 'Test Note 1',
            content: '# Test Note 1\n\nContent 1',
            createdAt: '2023-01-01T00:00:00.000Z',
            updatedAt: '2023-01-01T00:00:00.000Z',
          },
          {
            id: 'note-2',
            title: 'Test Note 2',
            content: '# Test Note 2\n\nContent 2',
            createdAt: '2023-01-02T00:00:00.000Z',
            updatedAt: '2023-01-02T00:00:00.000Z',
          },
        ],
        currentNoteId: 'note-1',
        editedContent: null,
        actions: useNotesStore.getState().actions,
      });
    });

    store = useNotesStore.getState();
  });

  describe('Initial State', () => {
    it('should initialize with the correct state', () => {
      expect(store.notes).toHaveLength(2);
      expect(store.currentNoteId).toBe('note-1');
      expect(store.editedContent).toBeNull();
    });
  });

  describe('fetchNotes', () => {
    it('should fetch notes successfully', async () => {
      const mockNotes = [
        {
          id: '1',
          title: 'Note 1',
          content: '# Note 1\n\nContent',
          createdAt: '2023-01-01',
          updatedAt: '2023-01-01',
        },
        {
          id: '2',
          title: 'Note 2',
          content: '# Note 2\n\nContent',
          createdAt: '2023-01-02',
          updatedAt: '2023-01-02',
        },
      ];

      (api.getNotes as jest.Mock).mockResolvedValue(mockNotes);

      await store.actions.fetchNotes();

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toEqual(mockNotes);
      expect(updatedStore.isLoading).toBe(false);
      expect(updatedStore.error).toBeNull();
    });

    it('should handle fetch error', async () => {
      const errorMessage = 'Failed to fetch notes';
      (api.getNotes as jest.Mock).mockRejectedValue(new Error(errorMessage));

      await store.actions.fetchNotes();

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.error).toBe(errorMessage);
      expect(updatedStore.isLoading).toBe(false);
    });

    it('should set loading state during fetch', async () => {
      let resolvePromise: (value: unknown[]) => void;
      const promise = new Promise<unknown[]>((resolve) => {
        resolvePromise = resolve;
      });
      (api.getNotes as jest.Mock).mockReturnValue(promise);

      const fetchPromise = store.actions.fetchNotes();

      // Check loading state is set
      const loadingStore = useNotesStore.getState();
      expect(loadingStore.isLoading).toBe(true);
      expect(loadingStore.error).toBeNull();

      // Resolve the promise
      resolvePromise!([]);
      await fetchPromise;

      // Check loading state is cleared
      const finalStore = useNotesStore.getState();
      expect(finalStore.isLoading).toBe(false);
    });
  });

  describe('createNote', () => {
    it('should create a new note with correct data', async () => {
      const store = useNotesStore;
      const { actions } = store.getState();

      // Mock the successful API call
      (api.createNote as jest.Mock).mockResolvedValue({
        id: 'note-3',
        title: 'New Note',
        content: '# New Note\n\n',
        createdAt: '2023-01-03T00:00:00.000Z',
        updatedAt: '2023-01-03T00:00:00.000Z',
      });

      const newNoteId = await actions.createNote();
      const updatedStore = useNotesStore.getState();

      expect(updatedStore.notes).toHaveLength(3);
      expect(updatedStore.currentNoteId).toBe(newNoteId);
      expect(updatedStore.editedContent).toBe('# New Note\n\n');

      const newNote = updatedStore.notes.find((note) => note.id === newNoteId);
      expect(newNote).toBeDefined();
      expect(newNote?.title).toBe('New Note');
      expect(newNote?.content).toBe('# New Note\n\n');
    });

    it('should return the ID of the newly created note', async () => {
      const store = useNotesStore;
      const { actions } = store.getState();
      const newNoteId = await actions.createNote();
      expect(newNoteId).toBe('note-3');
    });

    it('should handle createNote error', async () => {
      const errorMessage = 'Failed to create note';
      (api.createNote as jest.Mock).mockRejectedValue(new Error(errorMessage));

      const newNoteId = await store.actions.createNote();

      expect(newNoteId).toBeNull();
      const updatedStore = useNotesStore.getState();
      expect(updatedStore.error).toBe(errorMessage);
    });
  });

  describe('updateNote', () => {
    it('should update note content and title', async () => {
      const noteId = 'note-1';
      const newContent = '# Updated Title\n\nNew content';

      // Mock the successful API call
      (api.updateNote as jest.Mock).mockResolvedValue({
        id: noteId,
        title: 'Updated Title',
        content: newContent,
        createdAt: '2023-01-01T00:00:00.000Z',
        updatedAt: '2023-01-03T00:00:00.000Z',
      });

      await store.actions.updateNote(noteId, newContent);

      const updatedStore = useNotesStore.getState();
      const updatedNote = updatedStore.notes.find((note) => note.id === noteId);

      expect(updatedNote?.title).toBe('Updated Title');
      expect(updatedNote?.content).toBe(newContent);
      expect(updatedStore.editedContent).toBeNull();
    });

    it('should not update any note if ID does not exist', async () => {
      const initialNotes = [...store.notes];

      await store.actions.updateNote('non-existent-id', 'New content');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toEqual(initialNotes);
    });

    it('should handle updateNote error', async () => {
      const errorMessage = 'Failed to update note';
      (api.updateNote as jest.Mock).mockRejectedValue(new Error(errorMessage));

      await store.actions.updateNote('note-1', 'New content');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.error).toBe(errorMessage);
    });
  });

  describe('deleteNote', () => {
    it('should delete a note by ID', async () => {
      // Mock the successful API call
      (api.deleteNote as jest.Mock).mockResolvedValue(undefined);

      await store.actions.deleteNote('note-1');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toHaveLength(1);
      expect(updatedStore.notes[0].id).toBe('note-2');
    });

    it('should update currentNoteId when deleting current note', async () => {
      await store.actions.deleteNote('note-1');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.currentNoteId).toBe('note-2');
      expect(updatedStore.editedContent).toBeNull();
    });

    it('should set currentNoteId to null if all notes are deleted', async () => {
      await store.actions.deleteNote('note-1');
      await store.actions.deleteNote('note-2');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toHaveLength(0);
      expect(updatedStore.currentNoteId).toBeNull();
    });

    it('should not change state if note ID does not exist', async () => {
      const initialState = {
        notes: [...store.notes],
        currentNoteId: store.currentNoteId,
      };

      await store.actions.deleteNote('non-existent-id');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toEqual(initialState.notes);
      expect(updatedStore.currentNoteId).toBe(initialState.currentNoteId);
    });

    it('should handle deleteNote error', async () => {
      const errorMessage = 'Failed to delete note';
      (api.deleteNote as jest.Mock).mockRejectedValue(new Error(errorMessage));

      await store.actions.deleteNote('note-1');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.error).toBe(errorMessage);
    });
  });

  describe('setCurrentNote', () => {
    it('should update currentNoteId', () => {
      store.actions.setCurrentNote('note-2');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.currentNoteId).toBe('note-2');
    });

    it('should clear editedContent when changing notes', () => {
      // First set editing state
      store.actions.setEditedContent('Some edited content');
      expect(useNotesStore.getState().editedContent).toBe(
        'Some edited content'
      );

      // Then change note
      store.actions.setCurrentNote('note-2');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.editedContent).toBeNull();
    });

    it('should handle null ID', () => {
      store.actions.setCurrentNote(null);

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.currentNoteId).toBeNull();
    });
  });

  describe('setEditedContent', () => {
    it('should update editedContent state', () => {
      const content = 'Edited content';
      store.actions.setEditedContent(content);

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.editedContent).toBe(content);
    });

    it('should handle null content', () => {
      // First set some content
      store.actions.setEditedContent('Some content');

      // Then set to null
      store.actions.setEditedContent(null);

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.editedContent).toBeNull();
    });
  });
});
