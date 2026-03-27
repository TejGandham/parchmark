// ui/src/features/notes/components/NotesLayout.tsx
import { Outlet, useLoaderData, useParams, Link } from 'react-router-dom';
import { Box, Flex } from '@chakra-ui/react';
import Header from '../../ui/components/Header';
import { CommandPalette } from '../../ui/components/CommandPalette';
import { Note } from '../../../types';
import '../../ui/styles/layout.css';

export default function NotesLayout() {
  const { notes } = useLoaderData() as { notes: Note[] };
  const { noteId } = useParams();

  return (
    <Box minH="100vh" bg="bg.canvas" className="bg-texture">
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
        <Header />
        <CommandPalette notes={notes} />

        <Box
          as="main"
          id="main-content"
          flex="1"
          p={noteId ? 6 : 0}
          overflowY={noteId ? 'auto' : 'hidden'}
          className="note-transition"
          aria-label="Note content"
        >
          <Outlet />
        </Box>
      </Flex>
    </Box>
  );
}
