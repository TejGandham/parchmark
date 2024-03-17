import { useState, useEffect } from 'react';
import { Note } from '../types';
import { loadNotes, saveNotes, loadCurrentNoteId, saveCurrentNoteId } from '../services/localStorage';

export const useNotesState = () => {
  const [notes, setNotes] = useState<Note[]>(loadNotes());
  const [currentNoteId, setCurrentNoteId] = useState<string>(loadCurrentNoteId());
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [editedTitle, setEditedTitle] = useState('');

  // Persist notes to localStorage whenever they change
  useEffect(() => {
    saveNotes(notes);
  }, [notes]);

  // Persist current note ID whenever it changes
  useEffect(() => {
    saveCurrentNoteId(currentNoteId);
  }, [currentNoteId]);

  const currentNote = notes.find(note => note.id === currentNoteId) || notes[0];

  const selectNote = (id: string) => {
    setCurrentNoteId(id);
  };

  const createNewNote = () => {
    const defaultTitle = 'New Note';
    const newNote: Note = {
      id: Date.now().toString(),
      title: defaultTitle,
      content: `# ${defaultTitle}\n\nStart writing here...`,
    };
    setNotes([...notes, newNote]);
    setCurrentNoteId(newNote.id);
    
    // Set the edited content and title for immediate editing
    setEditedTitle(defaultTitle);
    setEditedContent(newNote.content);
    setIsEditing(true);
  };

  const deleteNote = (id: string) => {
    const filteredNotes = notes.filter(note => note.id !== id);

    setNotes(filteredNotes);

    // If we're deleting the currently selected note, we need to select another note
    if (currentNoteId === id) {
      // If there are any notes left, select the first one, otherwise set to empty
      if (filteredNotes.length > 0) {
        setCurrentNoteId(filteredNotes[0].id);
      } else {
        setCurrentNoteId('');
        // Reset editing state when no notes are left
        setIsEditing(false);
      }
    }
  };

  const startEditing = () => {
    if (!currentNote) return;
    
    setIsEditing(true);
    setEditedContent(currentNote.content);
    setEditedTitle(currentNote.title);
  };

  const saveNote = () => {
    // Extract title from H1 heading if present
    let finalTitle = editedTitle;
    let finalContent = editedContent;
    
    // Check if content starts with a markdown H1 heading
    const h1Match = editedContent.match(/^#\s+(.+)($|\n)/);
    if (h1Match && h1Match[1]) {
      // Use the H1 content as the title
      finalTitle = h1Match[1].trim();
    }
    
    // Clean up the default template text if it's still there
    if (finalContent.includes('Start writing here...')) {
      finalContent = finalContent.replace('Start writing here...', '').trim();
      
      // If after removing template text we end up with just the title, add a newline
      if (finalContent.trim() === `# ${finalTitle}`) {
        finalContent = `# ${finalTitle}\n\n`;
      }
    }
    
    setNotes(
      notes.map(note =>
        note.id === currentNoteId ? { ...note, content: finalContent, title: finalTitle } : note
      )
    );
    setIsEditing(false);
  };

  return {
    notes,
    currentNoteId,
    currentNote,
    isEditing,
    editedContent,
    editedTitle,
    setEditedContent,
    setEditedTitle,
    selectNote,
    createNewNote,
    deleteNote,
    startEditing,
    saveNote,
  };
};