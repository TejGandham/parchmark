import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Note } from '../types';
import {
  loadNotes,
  saveNotes,
  loadCurrentNoteId,
  saveCurrentNoteId,
} from '../services/localStorage';

export const useNotesState = () => {
  const [notes, setNotes] = useState<Note[]>(loadNotes());
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [editedTitle, setEditedTitle] = useState('');

  const { noteId } = useParams<{ noteId?: string }>();
  const navigate = useNavigate();

  // If there's a noteId in the URL, use it; otherwise use the stored id or the first note
  const [currentNoteId, setCurrentNoteId] = useState<string>(() => {
    if (noteId) return noteId;

    const savedId = loadCurrentNoteId();
    // Make sure the saved ID exists in our notes
    if (savedId && notes.some((note) => note.id === savedId)) {
      return savedId;
    }
    // Fall back to the first note if available
    return notes.length > 0 ? notes[0].id : '';
  });

  // Sync currentNoteId with the URL parameter
  useEffect(() => {
    if (noteId && noteId !== currentNoteId) {
      setCurrentNoteId(noteId);
    }
  }, [noteId, currentNoteId]);

  // REMOVED automatic URL updating effect - we'll only rely on explicit navigation

  // Persist notes to localStorage whenever they change
  useEffect(() => {
    saveNotes(notes);
  }, [notes]);

  // Persist current note ID whenever it changes
  useEffect(() => {
    saveCurrentNoteId(currentNoteId);
  }, [currentNoteId]);

  const currentNote =
    notes.find((note) => note.id === currentNoteId) || notes[0];

  const selectNote = (id: string) => {
    // Only navigate if we're not already viewing this note
    if (id !== currentNoteId) {
      setCurrentNoteId(id);
      navigate(`/notes/${id}`);
    }
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
    navigate(`/notes/${newNote.id}`);

    // Set the edited content and title for immediate editing
    setEditedTitle(defaultTitle);
    setEditedContent(newNote.content);
    setIsEditing(true);
  };

  const deleteNote = (id: string) => {
    const filteredNotes = notes.filter((note) => note.id !== id);

    setNotes(filteredNotes);

    // If we're deleting the currently selected note, we need to select another note
    if (currentNoteId === id) {
      // If there are any notes left, select the first one, otherwise go to /notes
      if (filteredNotes.length > 0) {
        const newSelectedId = filteredNotes[0].id;
        setCurrentNoteId(newSelectedId);
        navigate(`/notes/${newSelectedId}`);
      } else {
        setCurrentNoteId('');
        navigate('/notes');
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

    const updatedNotes = notes.map((note) =>
      note.id === currentNoteId
        ? { ...note, content: finalContent, title: finalTitle }
        : note
    );

    setNotes(updatedNotes);
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
