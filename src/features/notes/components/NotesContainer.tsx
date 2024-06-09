import { Box, Flex, Heading } from '@chakra-ui/react';
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

  const { isSidebarOpen, toggleSidebar } = useSidebarState();

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
