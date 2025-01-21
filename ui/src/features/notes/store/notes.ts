import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import {
  extractTitleFromMarkdown,
  formatNoteContent,
  createEmptyNoteContent,
} from '../../../services/markdownService';
import * as api from '../../../services/api';
import { Note } from '../../../types';

export type NotesState = {
  notes: Note[];
  currentNoteId: string | null;
  editedContent: string | null;
  isLoading: boolean;
  error: string | null;
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
    actions: {
      fetchNotes: async () => {
        set({ isLoading: true, error: null });
        try {
          const notes = await api.getNotes();
          set({ notes, isLoading: false });
        } catch (error: unknown) {
          const errorMessage =
            error instanceof Error ? error.message : 'An error occurred';
          set({ error: errorMessage, isLoading: false });
        }
      },
      createNote: async () => {
        const content = createEmptyNoteContent();
        const title = extractTitleFromMarkdown(content);
        try {
          const newNote = await api.createNote({ title, content });
          set((state) => {
            state.notes.push(newNote);
            state.currentNoteId = newNote.id;
            state.editedContent = content;
          });
          return newNote.id;
        } catch (error: unknown) {
          const errorMessage =
            error instanceof Error ? error.message : 'An error occurred';
          set({ error: errorMessage });
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
            }
          });
        } catch (error: unknown) {
          const errorMessage =
            error instanceof Error ? error.message : 'An error occurred';
          set({ error: errorMessage });
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
          const errorMessage =
            error instanceof Error ? error.message : 'An error occurred';
          set({ error: errorMessage });
        }
      },
      setCurrentNote: (id) => {
        set((state) => {
          state.editedContent = null;
          state.currentNoteId = id;
        });
      },
      setEditedContent: (content) => {
        set({ editedContent: content });
      },
    },
  }))
);
