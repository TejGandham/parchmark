// ui/src/features/notes/store/notesUI.ts
import { create } from 'zustand';

export type NotesUIState = {
  editedContent: string | null;
  setEditedContent: (content: string | null) => void;
};

export const useNotesUIStore = create<NotesUIState>((set) => ({
  editedContent: null,
  setEditedContent: (content) => set({ editedContent: content }),
}));
