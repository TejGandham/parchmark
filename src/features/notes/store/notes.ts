import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import {
  DEFAULT_NOTES,
  extractTitleFromMarkdown,
  formatNoteContent,
} from '../../../utils/constants';
import { Note } from '../../../types';

export type NotesState = {
  notes: Note[];
  currentNoteId: string | null;
  editedContent: string | null;
  actions: {
    createNote: () => string;
    updateNote: (id: string, content: string) => void;
    deleteNote: (id: string) => void;
    setCurrentNote: (id: string | null) => void;
    setEditedContent: (content: string | null) => void;
  };
};

// Initialize with default notes if storage is empty
export const useNotesStore = create<NotesState>()(
  persist(
    immer((set) => ({
      notes: DEFAULT_NOTES,
      currentNoteId: DEFAULT_NOTES.length > 0 ? DEFAULT_NOTES[0].id : null,
      editedContent: null,
      actions: {
        createNote: () => {
          const id = `note-${Date.now()}`;
          const timestamp = new Date().toISOString();
          const content = '# New Note\n\n';

          set((state) => {
            state.notes.push({
              id,
              title: 'New Note',
              content,
              createdAt: timestamp,
              updatedAt: timestamp,
            });
            state.currentNoteId = id;
            // Immediately set edited content to put note in edit mode
            state.editedContent = content;
          });

          return id;
        },

        updateNote: (id, content) => {
          set((state) => {
            const noteIndex = state.notes.findIndex((note) => note.id === id);
            if (noteIndex !== -1) {
              // Extract title and format content using shared utility functions
              const title = extractTitleFromMarkdown(content);
              const formattedContent = formatNoteContent(content);

              state.notes[noteIndex].content = formattedContent;
              state.notes[noteIndex].title = title;
              state.notes[noteIndex].updatedAt = new Date().toISOString();
              state.editedContent = null;
            }
          });
        },

        deleteNote: (id) => {
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
        },

        setCurrentNote: (id) => {
          set((state) => {
            state.currentNoteId = id;

            // We want to exit edit mode when changing notes
            // but don't reset when creating a new note (which sets editedContent)
            if (id && state.currentNoteId !== id) {
              state.editedContent = null;
            }
          });
        },

        setEditedContent: (content) => {
          set((state) => {
            state.editedContent = content;
          });
        },
      },
    })),
    { name: 'parchmark-notes' }
  )
);
