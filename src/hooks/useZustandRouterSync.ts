import { useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useNotesStore } from '../store';

/**
 * This hook synchronizes the URL/route with the Zustand store state
 * It is responsible for:
 * 1. Setting the current note in store based on the URL param
 * 2. Handling navigation after store operations like create/delete
 * 3. Providing access to current note data and editing state
 */
export const useZustandRouterSync = () => {
  const params = useParams();
  const navigate = useNavigate();

  // Get data from notes store
  const notes = useNotesStore((state) => state.notes);
  const currentNoteId = useNotesStore((state) => state.currentNoteId);
  const editedContent = useNotesStore((state) => state.editedContent);
  const storeActions = useNotesStore((state) => state.actions);

  // Compute derived state
  const currentNote = useMemo(
    () => notes.find((note) => note.id === currentNoteId) || null,
    [notes, currentNoteId]
  );

  const isEditing = editedContent !== null;

  // Sync route parameter to store
  useEffect(() => {
    const noteId = params.noteId;
    if (noteId && noteId !== currentNoteId) {
      // Check if note exists before setting it as current
      const noteExists = notes.some((note) => note.id === noteId);
      if (noteExists) {
        storeActions.setCurrentNote(noteId);
      } else {
        // Redirect to the first note or home if the note doesn't exist
        navigate(notes.length > 0 ? `/notes/${notes[0].id}` : '/', {
          replace: true,
        });
      }
    }
  }, [params.noteId, currentNoteId, notes, storeActions, navigate]);

  // Wrap store actions with navigation
  const wrappedActions = useMemo(
    () => ({
      createNote: () => {
        const newNoteId = storeActions.createNote();
        navigate(`/notes/${newNoteId}`);
        return newNoteId;
      },
      deleteNote: (id: string) => {
        // Before deleting, check if we need to navigate
        const willNeedNavigation = id === currentNoteId;
        const nextNoteId =
          notes.length > 1 ? notes.find((note) => note.id !== id)?.id : null;

        storeActions.deleteNote(id);

        // Navigate if needed
        if (willNeedNavigation) {
          navigate(nextNoteId ? `/notes/${nextNoteId}` : '/', {
            replace: true,
          });
        }
      },
      updateNote: storeActions.updateNote,
      setCurrentNote: (id: string | null) => {
        storeActions.setCurrentNote(id);
        if (id) {
          navigate(`/notes/${id}`);
        }
      },
      setEditedContent: storeActions.setEditedContent,
    }),
    [storeActions, navigate, currentNoteId, notes]
  );

  return {
    notes,
    currentNoteId,
    currentNote,
    isEditing,
    editedContent,
    actions: wrappedActions,
  };
};
