import { useEffect, useMemo, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useNotesStore } from '../../../store';
import { Note } from '../../../types';

/**
 * Custom hook that synchronizes URL parameters with store state
 * Simplifies routing by separating concerns:
 * 1. URL → Store: One-way sync from URL parameters to store state
 * 2. Actions → Navigation: Explicit navigation after state changes
 */
export const useStoreRouterSync = () => {
  // Router hooks
  const params = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  // Get store state with optimized selectors
  const notes = useNotesStore((state) => state.notes);
  const currentNoteId = useNotesStore((state) => state.currentNoteId);
  const editedContent = useNotesStore((state) => state.editedContent);
  const storeActions = useNotesStore((state) => state.actions);

  // Derived state with proper memoization and safety checks
  const currentNote = useMemo<Note | null>(() => {
    // CRITICAL FIX: Check that notes is an array before using array methods
    // This handles the case when notes might be undefined during initial load
    return Array.isArray(notes) && currentNoteId
      ? notes.find((note) => note.id === currentNoteId) || null
      : null;
  }, [notes, currentNoteId]);

  const isEditing = editedContent !== null;

  // URL → Store: One-way synchronization
  useEffect(() => {
    // Skip synchronization if notes is not yet available (during initial load)
    if (!Array.isArray(notes)) {
      return;
    }

    const noteId = params.noteId;
    const pathname = location.pathname;

    // Only handle route synchronization here, not navigation
    if (noteId) {
      // CRITICAL FIX: Safely check if note exists
      const noteExists = notes.some((note) => note.id === noteId);

      if (noteExists) {
        // CRITICAL FIX: Check if storeActions and setCurrentNote exist before calling
        // This prevents errors during initial hydration when the store might not be fully initialized
        if (storeActions && typeof storeActions.setCurrentNote === 'function') {
          // ALWAYS force the current note to be set from the URL parameter
          // This is critical for proper hydration on direct URL access
          storeActions.setCurrentNote(noteId);
        }
      } else if (notes.length > 0) {
        // Redirect if note doesn't exist
        navigate(`/notes/${notes[0].id}`, { replace: true });
      } else {
        navigate('/not-found', { replace: true });
      }
    } else if (pathname === '/notes' && notes.length > 0) {
      navigate(`/notes/${notes[0].id}`, { replace: true });
    }
  }, [
    // Don't include currentNoteId in the dependencies
    // This prevents unnecessary re-runs when the store changes
    params.noteId,
    location.pathname,
    notes,
    storeActions,
    navigate,
  ]);

  // Simplified action handlers with explicit navigation
  const navigateToNote = useCallback(
    (noteId: string | null) => {
      navigate(noteId ? `/notes/${noteId}` : '/notes');
    },
    [navigate]
  );

  const findNextNoteId = useCallback(
    (deletedId: string): string | null => {
      if (notes.length <= 1) return null;

      const index = notes.findIndex((note) => note.id === deletedId);
      if (index === -1) return null;

      // Return the next note if available, otherwise the previous
      const nextIndex = index < notes.length - 1 ? index + 1 : index - 1;
      return notes[nextIndex]?.id || null;
    },
    [notes]
  );

  // Simplified action wrappers
  const actions = useMemo(() => {
    // CRITICAL FIX: Add safety wrapper for each action to handle initialization state
    // This prevents errors when actions are accessed before store is fully initialized
    const safeStoreAction = <T extends (...args: unknown[]) => unknown>(
      action: T | undefined,
      fallback: unknown = undefined
    ) => {
      return (...args: Parameters<T>): ReturnType<T> | undefined => {
        if (typeof action === 'function') {
          return action(...args);
        }
        return fallback;
      };
    };

    return {
      // Create note and navigate with safety check
      createNote: () => {
        // Check if storeActions exists and has the necessary method
        if (storeActions && typeof storeActions.createNote === 'function') {
          const newId = storeActions.createNote();
          navigateToNote(newId);
          return newId;
        }
        return null;
      },

      // Delete note with simplified navigation logic and safety check
      deleteNote: (id: string) => {
        if (!storeActions || typeof storeActions.deleteNote !== 'function')
          return;

        const isCurrentNote = id === currentNoteId;
        const nextId = isCurrentNote ? findNextNoteId(id) : null;

        storeActions.deleteNote(id);

        if (isCurrentNote) {
          navigateToNote(nextId);
        }
      },

      // Direct pass-through for simple actions with safety checks
      updateNote: safeStoreAction(storeActions?.updateNote),

      // Set current note with navigation and safety check
      setCurrentNote: (id: string | null) => {
        // Always set current note and navigate, even if it's the same note
        if (storeActions && typeof storeActions.setCurrentNote === 'function') {
          storeActions.setCurrentNote(id);
        }
        navigateToNote(id);
      },

      // Simple pass-through with safety check
      setEditedContent: safeStoreAction(storeActions?.setEditedContent),
    };
  }, [storeActions, navigateToNote, findNextNoteId, currentNoteId]);

  return {
    notes,
    currentNoteId,
    currentNote,
    isEditing,
    editedContent,
    actions,
  };
};

