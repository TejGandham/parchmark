import { Box, Flex } from '@chakra-ui/react';
import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useUIStore } from '../../../store';
import { useStoreRouterSync } from '../../../hooks/useStoreRouterSync';
import Header from '../../../components/layout/Header';
import Sidebar from '../../../components/layout/Sidebar';
import NoteContent from '../../../components/notes/NoteContent';
import { COLORS } from '../../../utils/constants';
import '../../../components/layout/styles/layout.css';

const NotesContainer = () => {
  // UI state from store
  const isSidebarOpen = useUIStore((state) => state.isSidebarOpen);
  const toggleSidebar = useUIStore((state) => state.actions.toggleSidebar);

  // Use our custom hook for routing/store synchronization
  const {
    notes,
    currentNoteId,
    currentNote,
    isEditing,
    editedContent,
    actions,
  } = useStoreRouterSync();

  const { noteId } = useParams<{ noteId?: string }>();
  const navigate = useNavigate();

  // Handle navigation case where note ID in URL doesn't exist
  useEffect(() => {
    // Only check for invalid noteId if we have a noteId in the URL
    if (noteId) {
      // Check if this noteId exists in our notes collection
      const noteExists = notes.some((note) => note.id === noteId);

      // If the note doesn't exist, redirect to 404 page
      if (!noteExists) {
        navigate('/not-found', { replace: true });
      }
    } else if (notes.length > 0 && window.location.pathname === '/notes') {
      // If we're at the /notes route with no specific note ID but we have notes,
      // navigate to the first note
      navigate(`/notes/${notes[0].id}`, { replace: true });
    }
  }, [noteId, notes, navigate]);

  return (
    <Box minH="100vh" bg={COLORS.bgColor} className="bg-texture">
      <Flex h="100vh" flexDirection="column">
        <Header toggleSidebar={toggleSidebar} />

        <Flex flex="1" overflow="hidden">
          {isSidebarOpen && (
            <Sidebar
              notes={notes}
              currentNoteId={currentNoteId || ''}
              onSelectNote={actions.setCurrentNote}
              onCreateNote={actions.createNote}
              onDeleteNote={actions.deleteNote}
            />
          )}

          <Box flex="1" p={6} overflowY="auto" className="note-transition">
            <NoteContent
              currentNote={currentNote}
              isEditing={isEditing}
              editedContent={editedContent || ''}
              setEditedContent={actions.setEditedContent}
              startEditing={() =>
                actions.setEditedContent(currentNote?.content || '')
              }
              saveNote={() =>
                currentNoteId &&
                actions.updateNote(currentNoteId, editedContent || '')
              }
              createNewNote={actions.createNote}
            />
          </Box>
        </Flex>
      </Flex>
    </Box>
  );
};

export default NotesContainer;
