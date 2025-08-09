import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { DEFAULT_NOTES } from '../../../utils/constants';
import {
  extractTitleFromMarkdown,
  formatNoteContent,
  createEmptyNoteContent,
} from '../../../services/markdownService';
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
      notes: Array.isArray(DEFAULT_NOTES) ? DEFAULT_NOTES : [],
      currentNoteId:
        Array.isArray(DEFAULT_NOTES) && DEFAULT_NOTES.length > 0
          ? DEFAULT_NOTES[0].id
          : null,
      editedContent: null,
      // CRITICAL: This actions object must always be defined synchronously
      // to prevent errors during initial hydration from localStorage
      actions: {
        createNote: () => {
          const id = `note-${Date.now()}`;
          const timestamp = new Date().toISOString();
          const content = createEmptyNoteContent();

          set((state) => {
            // Ensure notes is initialized as an array
            if (!Array.isArray(state.notes)) {
              state.notes = [];
            }

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
            // Ensure notes is initialized as an array
            if (!Array.isArray(state.notes)) {
              state.notes = [];
              return;
            }

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
            // Ensure notes is initialized as an array
            if (!Array.isArray(state.notes)) {
              state.notes = [];
              return;
            }

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
            // CRITICAL FIX: Always reset edited content on ANY setCurrentNote call
            // This ensures switching notes from any source works properly
            state.editedContent = null;

            // Update the current note ID
            state.currentNoteId = id;
          });
        },

        setEditedContent: (content) => {
          set((state) => {
            state.editedContent = content;
          });
        },
      },
    })),
    {
      name: 'parchmark-notes',
      // Add configuration to ensure actions are always available during hydration
      merge: (persistedState, currentState) => {
        // Make sure we always preserve the actions from the current state
        // This prevents actions from being undefined during hydration
        return {
          ...persistedState,
          actions: currentState.actions,
        };
      },
    }
  )
);
