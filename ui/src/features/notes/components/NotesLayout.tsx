// ui/src/features/notes/components/NotesLayout.tsx
import { useEffect } from 'react';
import {
  Outlet,
  useLoaderData,
  useParams,
  Link,
  useMatch,
} from 'react-router-dom';
import { Box, Flex, VStack, Text, Heading, Icon } from '@chakra-ui/react';
import { EditIcon } from '@chakra-ui/icons';
import { useUIStore } from '../../../store';
import Header from '../../ui/components/Header';
import { CommandPalette } from '../../ui/components/CommandPalette';
import { Note } from '../../../types';
import '../../ui/styles/layout.css';

export default function NotesLayout() {
  const { notes } = useLoaderData() as { notes: Note[] };
  const { noteId } = useParams();

  const isExplore = useMatch('/notes/explore');
  const openPalette = useUIStore((s) => s.actions.openPalette);

  useEffect(() => {
    if (!noteId && !isExplore) {
      openPalette();
    }
  }, [noteId, isExplore, openPalette]);

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
          p={isExplore ? 0 : 6}
          overflowY={isExplore ? 'hidden' : 'auto'}
          className="note-transition"
          aria-label="Note content"
        >
          {noteId || isExplore ? (
            <Outlet />
          ) : (
            <VStack spacing={4} align="center" justify="center" h="100%" px={8}>
              <Box
                w="100px"
                h="100px"
                bg="primary.50"
                borderRadius="full"
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Icon as={EditIcon} fontSize="4xl" color="primary.300" />
              </Box>
              <Heading
                size="md"
                color="text.primary"
                fontFamily="'Playfair Display', serif"
              >
                Click the search bar above to find notes
              </Heading>
              <Text fontSize="sm" color="text.muted">
                {notes.length} {notes.length === 1 ? 'note' : 'notes'} available
              </Text>
              <Link to="/notes/explore">
                <Text
                  fontSize="sm"
                  color="primary.600"
                  textDecoration="underline dotted"
                  _hover={{ color: 'primary.800' }}
                  data-testid="browse-all-notes-link"
                >
                  or browse all notes →
                </Text>
              </Link>
            </VStack>
          )}
        </Box>
      </Flex>
    </Box>
  );
}
