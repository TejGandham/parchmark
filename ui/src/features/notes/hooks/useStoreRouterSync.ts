import { useEffect, useMemo, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useNotesStore, useAuthStore } from '../../../store';
import { Note } from '../../../types';

export const useStoreRouterSync = () => {
  const params = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const {
    notes,
    currentNoteId,
    editedContent,
    actions: storeActions,
  } = useNotesStore();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && storeActions) {
      storeActions.fetchNotes();
    }
  }, [isAuthenticated, storeActions]);

  const currentNote = useMemo<Note | null>(() => {
    return Array.isArray(notes) && currentNoteId
      ? notes.find((note) => note.id === currentNoteId) || null
      : null;
  }, [notes, currentNoteId]);

  const isEditing = editedContent !== null;

  useEffect(() => {
    if (!Array.isArray(notes)) {
      return;
    }

    const noteId = params.noteId;
    const pathname = location.pathname;

    if (noteId) {
      const noteExists = notes.some((note) => note.id === noteId);

      if (noteExists) {
        if (storeActions && typeof storeActions.setCurrentNote === 'function') {
          storeActions.setCurrentNote(noteId);
        }
      } else if (notes.length > 0) {
        navigate(`/notes/${notes[0].id}`, { replace: true });
      } else {
        // Let it be handled by the no-notes case in the component
      }
    } else if (pathname === '/notes' && notes.length > 0) {
      navigate(`/notes/${notes[0].id}`, { replace: true });
    }
  }, [params.noteId, location.pathname, notes, storeActions, navigate]);

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
      const nextIndex = index < notes.length - 1 ? index + 1 : index - 1;
      return notes[nextIndex]?.id || null;
    },
    [notes]
  );

  const actions = useMemo(() => {
    const safeStoreAction = <T extends (...args: any[]) => any>(
      action: T | undefined,
      fallback: any = undefined
    ) => {
      return async (
        ...args: Parameters<T>
      ): Promise<ReturnType<T> | undefined> => {
        if (typeof action === 'function') {
          return await action(...args);
        }
        return fallback;
      };
    };

    return {
      createNote: async () => {
        if (storeActions && typeof storeActions.createNote === 'function') {
          const newId = await storeActions.createNote();
          if (newId) {
            navigateToNote(newId);
          }
          return newId;
        }
        return null;
      },
      deleteNote: async (id: string) => {
        if (!storeActions || typeof storeActions.deleteNote !== 'function')
          return;
        const isCurrentNote = id === currentNoteId;
        const nextId = isCurrentNote ? findNextNoteId(id) : null;
        await storeActions.deleteNote(id);
        if (isCurrentNote) {
          navigateToNote(nextId);
        }
      },
      updateNote: safeStoreAction(storeActions?.updateNote),
      setCurrentNote: (id: string | null) => {
        if (storeActions && typeof storeActions.setCurrentNote === 'function') {
          storeActions.setCurrentNote(id);
        }
        navigateToNote(id);
      },
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
