import { act } from 'react';
import { beforeEach, describe, expect, it, jest } from '@jest/globals';
import {
  useNotesStore,
  NotesState,
} from '../../../../features/notes/store/notes';

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

  describe('createNote', () => {
    it('should create a new note with correct data', () => {
      const newNoteId = store.actions.createNote();

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toHaveLength(3);
      expect(updatedStore.currentNoteId).toBe(newNoteId);
      expect(updatedStore.editedContent).toBe('# New Note\n\n');

      const newNote = updatedStore.notes.find((note) => note.id === newNoteId);
      expect(newNote).toBeDefined();
      expect(newNote?.title).toBe('New Note');
      expect(newNote?.content).toBe('# New Note\n\n');
      expect(newNote?.createdAt).toBe(mockTimestamp);
      expect(newNote?.updatedAt).toBe(mockTimestamp);
    });

    it('should return the ID of the newly created note', () => {
      const newNoteId = store.actions.createNote();
      expect(newNoteId).toBe(`note-${mockDateNow}`);
    });
  });

  describe('updateNote', () => {
    it('should update note content and title', () => {
      const noteId = 'note-1';
      const newContent = '# Updated Title\n\nNew content';

      store.actions.updateNote(noteId, newContent);

      const updatedStore = useNotesStore.getState();
      const updatedNote = updatedStore.notes.find((note) => note.id === noteId);

      expect(updatedNote?.title).toBe('Updated Title');
      expect(updatedNote?.content).toBe(newContent);
      expect(updatedNote?.updatedAt).toBe(mockTimestamp);
      expect(updatedStore.editedContent).toBeNull();
    });

    it('should not update any note if ID does not exist', () => {
      const initialNotes = [...store.notes];

      store.actions.updateNote('non-existent-id', 'New content');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toEqual(initialNotes);
    });
  });

  describe('deleteNote', () => {
    it('should delete a note by ID', () => {
      store.actions.deleteNote('note-1');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toHaveLength(1);
      expect(updatedStore.notes[0].id).toBe('note-2');
    });

    it('should update currentNoteId when deleting current note', () => {
      store.actions.deleteNote('note-1');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.currentNoteId).toBe('note-2');
      expect(updatedStore.editedContent).toBeNull();
    });

    it('should set currentNoteId to null if all notes are deleted', () => {
      store.actions.deleteNote('note-1');
      store.actions.deleteNote('note-2');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toHaveLength(0);
      expect(updatedStore.currentNoteId).toBeNull();
    });

    it('should not change state if note ID does not exist', () => {
      const initialState = {
        notes: [...store.notes],
        currentNoteId: store.currentNoteId,
      };

      store.actions.deleteNote('non-existent-id');

      const updatedStore = useNotesStore.getState();
      expect(updatedStore.notes).toEqual(initialState.notes);
      expect(updatedStore.currentNoteId).toBe(initialState.currentNoteId);
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
