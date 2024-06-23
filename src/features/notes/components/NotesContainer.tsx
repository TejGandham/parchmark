import { Box, Flex } from '@chakra-ui/react';
import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useNotesState } from '../../../hooks/useNotesState';
import { useSidebarState } from '../../../hooks/useSidebarState';
import Header from '../../../components/layout/Header';
import Sidebar from '../../../components/layout/Sidebar';
import NoteContent from '../../../components/notes/NoteContent';
import { COLORS } from '../../../utils/constants';
import '../../../components/layout/styles/layout.css';

const NotesContainer = () => {
  const {
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
  } = useNotesState();

  const { noteId } = useParams<{ noteId?: string }>();
  const navigate = useNavigate();
  const { isSidebarOpen, toggleSidebar } = useSidebarState();

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
              currentNoteId={currentNoteId}
              onSelectNote={selectNote}
              onCreateNote={createNewNote}
              onDeleteNote={deleteNote}
            />
          )}

          <Box flex="1" p={6} overflowY="auto" className="note-transition">
            <NoteContent
              currentNote={currentNote}
              isEditing={isEditing}
              editedTitle={editedTitle}
              editedContent={editedContent}
              setEditedTitle={setEditedTitle}
              setEditedContent={setEditedContent}
              startEditing={startEditing}
              saveNote={saveNote}
              createNewNote={createNewNote}
            />
          </Box>
        </Flex>
      </Flex>
    </Box>
  );
};

export default NotesContainer;
