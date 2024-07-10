import { useEffect, useMemo } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useNotesStore } from '../../../store';

/**
 * This hook synchronizes the URL/route with the store state
 * It is responsible for:
 * 1. Setting the current note in store based on the URL param
 * 2. Handling navigation after store operations like create/delete
 * 3. Providing access to current note data and editing state
 * 4. Ensuring proper routing when notes don't exist or no specific note is selected
 */
export const useStoreRouterSync = () => {
  const params = useParams();
  const navigate = useNavigate();
  const location = useLocation();

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
    const pathname = location.pathname;

    // Case 1: We have a note ID in the URL
    if (noteId) {
      const noteExists = notes.some((note) => note.id === noteId);

      // If note exists and isn't current, set it as current
      if (noteExists && noteId !== currentNoteId) {
        storeActions.setCurrentNote(noteId);
      }
      // If note doesn't exist, redirect
      else if (!noteExists) {
        if (notes.length > 0) {
          navigate(`/notes/${notes[0].id}`, { replace: true });
        } else {
          navigate('/not-found', { replace: true });
        }
      }
    }
    // Case 2: We're at /notes with no specific ID but have notes
    else if (pathname === '/notes' && notes.length > 0) {
      navigate(`/notes/${notes[0].id}`, { replace: true });
    }
  }, [
    params.noteId,
    location.pathname,
    currentNoteId,
    notes,
    storeActions,
    navigate,
  ]);

  // Wrap store actions with navigation
  const wrappedActions = useMemo(
    () => ({
      createNote: () => {
        // Create the note in the store
        // Note: the store now handles setting editedContent
        const newNoteId = storeActions.createNote();

        // Navigate to the new note
        navigate(`/notes/${newNoteId}`);

        return newNoteId;
      },
      deleteNote: (id: string) => {
        // Before deleting, check if we need to navigate
        const willNeedNavigation = id === currentNoteId;

        // Find the index of the note being deleted
        const noteIndex = notes.findIndex((note) => note.id === id);

        // Determine the next note to navigate to
        let nextNoteId: string | null = null;
        if (notes.length > 1) {
          // Try to select the next note in the list, or fallback to the previous one
          const nextIndex =
            noteIndex < notes.length - 1 ? noteIndex + 1 : noteIndex - 1;
          nextNoteId = notes[nextIndex]?.id;
        }

        storeActions.deleteNote(id);

        // Navigate if needed
        if (willNeedNavigation) {
          navigate(nextNoteId ? `/notes/${nextNoteId}` : '/notes', {
            replace: true,
          });
        }
      },
      updateNote: storeActions.updateNote,
      setCurrentNote: (id: string | null) => {
        // Only navigate if the ID is different from current to avoid unnecessary rerenders
        if (id !== currentNoteId) {
          storeActions.setCurrentNote(id);

          if (id) {
            navigate(`/notes/${id}`);
          } else {
            navigate('/notes');
          }
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
