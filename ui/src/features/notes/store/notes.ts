import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import {
  extractTitleFromMarkdown,
  formatNoteContent,
  createEmptyNoteContent,
} from '../../../services/markdownService';
import * as api from '../../../services/api';
import { Note } from '../../../types';
import { handleError } from '../../../utils/errorHandler';

export type NotesState = {
  notes: Note[];
  currentNoteId: string | null;
  editedContent: string | null;
  isLoading: boolean;
  error: string | null;
  justCreatedNoteId: string | null; // Track recently created note to preserve edit mode
  actions: {
    fetchNotes: () => Promise<void>;
    createNote: () => Promise<string | null>;
    updateNote: (id: string, content: string) => Promise<void>;
    deleteNote: (id: string) => Promise<void>;
    setCurrentNote: (id: string | null) => void;
    setEditedContent: (content: string | null) => void;
  };
};

export const useNotesStore = create<NotesState>()(
  immer((set) => ({
    notes: [],
    currentNoteId: null,
    editedContent: null,
    isLoading: false,
    error: null,
    justCreatedNoteId: null,
    actions: {
      fetchNotes: async () => {
        set({ isLoading: true, error: null });
        try {
          const notes = await api.getNotes();
          set({ notes, isLoading: false });
        } catch (error: unknown) {
          const appError = handleError(error);
          set({ error: appError.message, isLoading: false });
        }
      },
      createNote: async () => {
        const content = createEmptyNoteContent();
        const title = extractTitleFromMarkdown(content);
        try {
          const newNote = await api.createNote({ title, content });
          set((state) => {
            state.notes.push(newNote);
            state.editedContent = content;
            state.justCreatedNoteId = newNote.id;
          });
          return newNote.id;
        } catch (error: unknown) {
          const appError = handleError(error);
          set({ error: appError.message });
          return null;
        }
      },
      updateNote: async (id, content) => {
        const formattedContent = formatNoteContent(content);
        try {
          const updatedNote = await api.updateNote(id, {
            content: formattedContent,
          });
          set((state) => {
            const noteIndex = state.notes.findIndex((note) => note.id === id);
            if (noteIndex !== -1) {
              state.notes[noteIndex] = updatedNote;
              state.editedContent = null;
              // Clear the just-created flag when note is saved
              if (state.justCreatedNoteId === id) {
                state.justCreatedNoteId = null;
              }
            }
          });
        } catch (error: unknown) {
          const appError = handleError(error);
          set({ error: appError.message });
        }
      },
      deleteNote: async (id) => {
        try {
          await api.deleteNote(id);
          set((state) => {
            const noteIndex = state.notes.findIndex((note) => note.id === id);
            if (noteIndex !== -1) {
              state.notes.splice(noteIndex, 1);
              if (state.currentNoteId === id) {
                state.currentNoteId =
                  state.notes.length > 0 ? state.notes[0].id : null;
                state.editedContent = null;
              }
            }
          });
        } catch (error: unknown) {
          const appError = handleError(error);
          set({ error: appError.message });
        }
      },
      setCurrentNote: (id) => {
        set((state) => {
          // Preserve edit mode if navigating to a just-created note
          if (state.justCreatedNoteId !== id) {
            state.editedContent = null;
          }
          state.currentNoteId = id;
          // Clear the flag once we've navigated to the note
          if (state.justCreatedNoteId === id) {
            state.justCreatedNoteId = null;
          }
        });
      },
      setEditedContent: (content) => {
        set({ editedContent: content });
      },
    },
  }))
);
