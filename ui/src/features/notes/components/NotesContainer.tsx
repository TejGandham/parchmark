import { Box, Flex, Link } from '@chakra-ui/react';
import { useUIStore } from '../../../store';
import { useStoreRouterSync } from '../hooks/useStoreRouterSync';
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
  // Access the entire store once to prevent infinite loops
  const uiStore = useUIStore();
  const isSidebarOpen = uiStore.isSidebarOpen;
  const toggleSidebar = uiStore.actions.toggleSidebar;

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
    <Box minH="100vh" bg="bg.canvas" className="bg-texture">
      {/* Skip to main content link for screen readers */}
      <Link
        href="#main-content"
        position="absolute"
        left="-9999px"
        zIndex="9999"
        p={3}
        bg="primary.500"
        color="white"
        borderRadius="md"
        _focus={{
          left: '10px',
          top: '10px',
        }}
      >
        Skip to main content
      </Link>

      <Flex h="100vh" flexDirection="column">
        <Header toggleSidebar={toggleSidebar} />

        <Flex flex="1" overflow="hidden">
          {isSidebarOpen && (
            <Box as="nav" aria-label="Notes navigation">
              <Sidebar
                notes={notes}
                currentNoteId={currentNoteId || ''}
                onSelectNote={actions.setCurrentNote}
                onCreateNote={actions.createNote}
                onDeleteNote={actions.deleteNote}
              />
            </Box>
          )}

          <Box
            as="main"
            id="main-content"
            flex="1"
            p={6}
            overflowY="auto"
            className="note-transition"
            aria-label="Note content"
          >
            <NoteContent {...noteContentProps} />
          </Box>
        </Flex>
      </Flex>
    </Box>
  );
};

export default NotesContainer;
