import { Box, Flex } from '@chakra-ui/react';
import { useUIStore } from '../../../store';
import { useStoreRouterSync } from '../hooks/useStoreRouterSync';
import { COLORS } from '../../../utils/constants';
import '../../ui/styles/layout.css';

// Direct imports from feature folders
import Header from '../../ui/components/Header';
import Sidebar from '../../ui/components/Sidebar';
import NoteContent from './NoteContent';

/**
 * Main container component for the notes feature
 * Orchestrates layout and state management between UI components
 */
const NotesContainer = () => {
  // Get UI state using selector pattern for better performance
  const isSidebarOpen = useUIStore((state) => state.isSidebarOpen);
  const toggleSidebar = useUIStore((state) => state.actions.toggleSidebar);

  // Centralized hook for all notes state + routing
  const {
    notes,
    currentNoteId,
    currentNote,
    isEditing,
    editedContent,
    actions,
  } = useStoreRouterSync();

  // Prepare props for NoteContent
  const noteContentProps = {
    currentNote,
    isEditing,
    editedContent: editedContent === null ? '' : editedContent,
    setEditedContent: actions.setEditedContent,
    startEditing: () => actions.setEditedContent(currentNote?.content || ''),
    saveNote: () => {
      if (currentNoteId && editedContent !== null) {
        actions.updateNote(currentNoteId, editedContent);
      }
    },
    createNewNote: actions.createNote,
  };

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
            <NoteContent {...noteContentProps} />
          </Box>
        </Flex>
      </Flex>
    </Box>
  );
};

export default NotesContainer;
