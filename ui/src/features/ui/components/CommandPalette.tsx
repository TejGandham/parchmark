import {
  useRef,
  useEffect,
  useState,
  useMemo,
  type MouseEvent,
  type MutableRefObject,
} from 'react';
import {
  Portal,
  Box,
  Input,
  Text,
  VStack,
  HStack,
} from '@chakra-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  useNavigate,
  useParams,
} from 'react-router-dom';
import { useUIStore } from '../store/ui';
import { Note, SimilarNote } from '../../../types';
import { filterNotes, sortNotes } from '../../../utils/dateGrouping';
import { formatCompactTime } from '../../../utils/compactTime';
import { getBlendedForYouNotes } from '../../../utils/noteScoring';
import { trackNoteAccess, getSimilarNotes } from '../../../services/api';
import { highlightKeyword } from './commandPaletteUtils';

interface CommandPaletteProps {
  notes?: Note[];
}

interface PaletteNoteItemProps {
  note: Note;
  searchQuery?: string;
  onSelect: (id: string) => void;
}

function PaletteNoteItem({
  note,
  searchQuery,
  onSelect,
}: PaletteNoteItemProps) {
  return (
    <HStack
      px={4}
      py={2}
      cursor="pointer"
      bg="transparent"
      _hover={{ bg: 'primary.50' }}
      transition="background 0.15s ease"
      onClick={() => onSelect(note.id)}
      spacing={3}
      data-testid="palette-note-item"
    >
      <Text
        fontSize="sm"
        noOfLines={1}
        flex={1}
        color="text.primary"
      >
        {searchQuery ? highlightKeyword(note.title, searchQuery) : note.title}
      </Text>
      <Text fontSize="xs" color="text.muted" flexShrink={0}>
        {formatCompactTime(note.updatedAt)}
      </Text>
    </HStack>
  );
}

export const CommandPalette = ({ notes = [] }: CommandPaletteProps) => {
  const isPaletteOpen = useUIStore((state) => state.isPaletteOpen);
  const closePalette = useUIStore((state) => state.actions.closePalette);
  const searchQuery = useUIStore((state) => state.paletteSearchQuery);
  const setSearchQuery = useUIStore(
    (state) => state.actions.setPaletteSearchQuery
  );
  const searchInputRef = useRef<HTMLInputElement>(
    null
  ) as MutableRefObject<HTMLInputElement | null>;
  const navigate = useNavigate();
  const { noteId: currentNoteId } = useParams<{ noteId: string }>();

  const [similarNotes, setSimilarNotes] = useState<SimilarNote[]>([]);

  const setSearchInputRef = (node: HTMLInputElement | null) => {
    searchInputRef.current = node;
    if (node) {
      node.focus();
    }
  };

  useEffect(() => {
    if (!isPaletteOpen || !currentNoteId) {
      setSimilarNotes([]);
      return;
    }

    let cancelled = false;
    getSimilarNotes(currentNoteId).then((result) => {
      if (!cancelled) {
        setSimilarNotes(result);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [isPaletteOpen, currentNoteId]);

  const recentNotes = useMemo(
    () => sortNotes(notes, 'lastModified', 'desc').slice(0, 5),
    [notes]
  );

  const forYouNotes = useMemo(
    () => getBlendedForYouNotes(notes, currentNoteId ?? null, similarNotes, 3),
    [notes, currentNoteId, similarNotes]
  );

  const filteredNotes = useMemo(
    () => (searchQuery ? filterNotes(notes, searchQuery) : []),
    [notes, searchQuery]
  );

  const isSearching = searchQuery.length > 0;

  useEffect(() => {
    if (isPaletteOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isPaletteOpen]);

  const handleSelect = (noteId: string) => {
    navigate(`/notes/${noteId}`);
    closePalette();
    trackNoteAccess(noteId);
  };

  const handleBackdropClick = (e: MouseEvent) => {
    if (e.target === e.currentTarget) closePalette();
  };

  return (
    <Portal>
      <AnimatePresence>
        {isPaletteOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            <Box
              position="fixed"
              top={0}
              left={0}
              right={0}
              bottom={0}
              bg="blackAlpha.600"
              backdropFilter="blur(4px)"
              zIndex={1400}
              onClick={handleBackdropClick}
              data-testid="command-palette-backdrop"
            />

            <Box
              role="dialog"
              aria-label="Command palette"
              position="fixed"
              top="15vh"
              left="50%"
              transform="translateX(-50%)"
              width={{ base: '90vw', md: '520px' }}
              maxHeight="60vh"
              bg="bg.surface"
              borderRadius="xl"
              boxShadow="xl"
              overflow="hidden"
              zIndex={1500}
              data-testid="command-palette"
            >
              <Input
                ref={setSearchInputRef}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="What are you looking for?"
                _placeholder={{ color: 'neutral.400' }}
                size="lg"
                border="none"
                borderBottom="1px solid"
                borderColor="border.default"
                borderRadius={0}
                _focus={{ borderColor: 'primary.300', boxShadow: 'none' }}
                data-testid="command-palette-search"
              />

              <VStack
                spacing={0}
                align="stretch"
                overflowY="auto"
                maxHeight="50vh"
              >
                {isSearching && (
                  <>
                    <Box
                      px={4}
                      py={1.5}
                      borderBottom="1px"
                      borderColor="neutral.200"
                      bg="neutral.100"
                    >
                      <Text
                        fontSize="xs"
                        color="text.muted"
                        data-testid="search-result-count"
                      >
                        {filteredNotes.length}{' '}
                        {filteredNotes.length === 1 ? 'result' : 'results'}
                      </Text>
                    </Box>
                    <AnimatePresence mode="popLayout">
                      {filteredNotes.map((note) => (
                        <motion.div
                          key={note.id}
                          layout
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.1 }}
                        >
                          <PaletteNoteItem
                            note={note}
                            searchQuery={searchQuery}
                            onSelect={handleSelect}
                          />
                        </motion.div>
                      ))}
                    </AnimatePresence>
                    {filteredNotes.length === 0 && (
                      <Box px={4} py={3} textAlign="center">
                        <Text
                          fontSize="sm"
                          color="text.muted"
                          data-testid="no-notes-found"
                        >
                          No notes found
                        </Text>
                      </Box>
                    )}
                  </>
                )}

                {!isSearching && notes.length === 0 && (
                  <VStack
                    spacing={4}
                    p={8}
                    align="center"
                    data-testid="zero-notes-state"
                  >
                    <Text color="text.muted" fontSize="sm">
                      No notes yet
                    </Text>
                  </VStack>
                )}

                {!isSearching && forYouNotes.length > 0 && (
                  <>
                    <Box
                      px={4}
                      py={1.5}
                      borderBottom="1px"
                      borderColor="secondary.100"
                      bg="secondary.50"
                    >
                      <Text
                        fontSize="xs"
                        fontWeight="bold"
                        color="section.forYou"
                        letterSpacing="wide"
                        data-testid="for-you-header"
                      >
                        FOR YOU
                      </Text>
                    </Box>
                    {forYouNotes.map((note) => (
                      <PaletteNoteItem
                        key={`fy-${note.id}`}
                        note={note}
                        onSelect={handleSelect}
                      />
                    ))}
                  </>
                )}

                {!isSearching && notes.length > 0 && (
                  <>
                    <Box
                      px={4}
                      py={1.5}
                      borderBottom="1px"
                      borderColor="primary.100"
                      bg="primary.50"
                    >
                      <Text
                        fontSize="xs"
                        fontWeight="bold"
                        color="section.recent"
                        letterSpacing="wide"
                        data-testid="recent-header"
                      >
                        RECENT
                      </Text>
                    </Box>
                    {recentNotes.map((note) => (
                      <PaletteNoteItem
                        key={note.id}
                        note={note}
                        onSelect={handleSelect}
                      />
                    ))}
                  </>
                )}
              </VStack>

              {!isSearching && notes.length > 0 && (
                <Box
                  px={4}
                  py={2}
                  borderTop="1px solid"
                  borderColor="border.default"
                  cursor="pointer"
                  _hover={{ bg: 'primary.50' }}
                  onClick={() => {
                    navigate('/notes');
                    closePalette();
                  }}
                  data-testid="browse-all-link"
                >
                  <Text fontSize="sm" color="primary.600">
                    Browse All Notes →
                  </Text>
                </Box>
              )}
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Portal>
  );
};
