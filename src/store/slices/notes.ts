import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import { DEFAULT_NOTES } from '../../utils/constants';
import { Note } from '../../types';

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

// Extract title from markdown content (first H1 heading)
const extractTitle = (content: string): string => {
  const titleMatch = content.match(/^#\s+(.+)$/m);
  return titleMatch ? titleMatch[1].trim() : 'Untitled Note';
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

          set((state) => {
            state.notes.push({
              id,
              title: 'New Note',
              content: '# New Note\n\nStart writing here...',
              createdAt: timestamp,
              updatedAt: timestamp,
            });
            state.currentNoteId = id;
            state.editedContent = null;
          });

          return id;
        },

        updateNote: (id, content) => {
          set((state) => {
            const noteIndex = state.notes.findIndex((note) => note.id === id);
            if (noteIndex !== -1) {
              state.notes[noteIndex].content = content;
              state.notes[noteIndex].title = extractTitle(content);
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
            state.editedContent = null;
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
