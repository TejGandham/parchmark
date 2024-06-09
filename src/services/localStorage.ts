import { Note } from '../types';
import { DEFAULT_NOTES } from '../utils/constants';

export const loadNotes = (): Note[] => {
  const savedNotes = localStorage.getItem('parchmark_notes');
  return savedNotes ? JSON.parse(savedNotes) : DEFAULT_NOTES;
};

export const saveNotes = (notes: Note[]): void => {
  localStorage.setItem('parchmark_notes', JSON.stringify(notes));
};

export const loadCurrentNoteId = (): string => {
  const savedId = localStorage.getItem('parchmark_current_note_id');
  return savedId || '1';
};

export const saveCurrentNoteId = (id: string): void => {
  localStorage.setItem('parchmark_current_note_id', id);
};
