// ui/src/features/notes/components/NotesLayout.tsx
import { useEffect } from 'react';
import {
  Outlet,
  useLoaderData,
  useNavigate,
  useParams,
  Link,
} from 'react-router-dom';
import { Box, Flex } from '@chakra-ui/react';
import { useUIStore } from '../../../store';
import Header from '../../ui/components/Header';
import Sidebar from '../../ui/components/Sidebar';
import { Note } from '../../../types';
import '../../ui/styles/layout.css';

export default function NotesLayout() {
  const { notes } = useLoaderData() as { notes: Note[] };
  const { noteId } = useParams();
  const navigate = useNavigate();

  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);
  const toggleSidebar = useUIStore((s) => s.actions.toggleSidebar);

  // Redirect to first note if none selected
  // Using firstNoteId to stabilize dependency - only triggers when noteId or firstNoteId changes,
  // not on every notes array reference change
  const firstNoteId = notes[0]?.id;
  useEffect(() => {
    if (!noteId && firstNoteId) {
      navigate(`/notes/${firstNoteId}`, { replace: true });
    }
  }, [noteId, firstNoteId, navigate]);

  return (
    <Box minH="100vh" bg="bg.canvas" className="bg-texture">
      {/* Skip to main content link for screen readers */}
      <Link
        to="#main-content"
        style={{
          position: 'absolute',
          left: '-9999px',
          zIndex: 9999,
        }}
      >
        Skip to main content
      </Link>

      <Flex h="100vh" flexDirection="column">
        <Header toggleSidebar={toggleSidebar} />

        <Flex flex="1" overflow="hidden">
          {isSidebarOpen && (
            <Box as="nav" aria-label="Notes navigation">
              <Sidebar notes={notes} currentNoteId={noteId || ''} />
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
            <Outlet />
          </Box>
        </Flex>
      </Flex>
    </Box>
  );
}
