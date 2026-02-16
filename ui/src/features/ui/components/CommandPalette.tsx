import {
  useRef,
  useEffect,
  useCallback,
  useState,
  useMemo,
  type MouseEvent,
  type MutableRefObject,
  type ReactNode,
} from 'react';
import {
  Portal,
  Box,
  Input,
  Text,
  VStack,
  HStack,
  Flex,
} from '@chakra-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import { useNavigate, useParams } from 'react-router-dom';
import { List, type RowComponentProps } from 'react-window';
import { useUIStore } from '../store/ui';
import { Note } from '../../../types';
import {
  filterNotes,
  sortNotes,
  groupNotesByDate,
  type SortOption,
  type SortDirection,
  type GroupedNotes,
} from '../../../utils/dateGrouping';
import { formatCompactTime } from '../../../utils/compactTime';
import { getForYouNotes } from '../../../utils/noteScoring';
import { trackNoteAccess } from '../../../services/api';

const VIRTUALIZATION_THRESHOLD = 50;
const PALETTE_ITEM_HEIGHT = 40;
const VIRTUAL_LIST_HEIGHT = 320;

interface CommandPaletteProps {
  notes?: Note[];
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function highlightKeyword(text: string, keyword: string): ReactNode {
  if (!keyword) return text;
  const escaped = escapeRegex(keyword);
  const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
  return parts.map((part, i) =>
    part.toLowerCase() === keyword.toLowerCase() ? (
      <Text as="strong" key={i} fontWeight="bold" color="primary.700">
        {part}
      </Text>
    ) : (
      part
    )
  );
}

interface PaletteNoteItemProps {
  note: Note;
  isActive: boolean;
  searchQuery?: string;
  onSelect: (id: string) => void;
}

function PaletteNoteItem({
  note,
  isActive,
  searchQuery,
  onSelect,
}: PaletteNoteItemProps) {
  return (
    <HStack
      px={4}
      py={2}
      cursor="pointer"
      bg={isActive ? 'primary.50' : 'transparent'}
      _hover={{ bg: isActive ? 'primary.100' : 'gray.50' }}
      onClick={() => onSelect(note.id)}
      spacing={3}
      data-testid="palette-note-item"
    >
      <Text
        fontSize="sm"
        noOfLines={1}
        flex={1}
        color={isActive ? 'primary.800' : 'text.primary'}
      >
        {searchQuery ? highlightKeyword(note.title, searchQuery) : note.title}
      </Text>
      <Text fontSize="xs" color="text.muted" flexShrink={0}>
        {formatCompactTime(note.updatedAt)}
      </Text>
    </HStack>
  );
}

interface VirtualRowData {
  notes: Note[];
  activeIndex: number;
  searchQuery: string;
  onSelect: (id: string) => void;
}

function VirtualNoteRow({
  index,
  style,
  notes,
  activeIndex,
  searchQuery,
  onSelect,
}: RowComponentProps<VirtualRowData>) {
  const note = notes[index];
  return (
    <Box style={style}>
      <PaletteNoteItem
        note={note}
        isActive={index === activeIndex}
        searchQuery={searchQuery}
        onSelect={onSelect}
      />
    </Box>
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

  const [isAllNotesExpanded, setIsAllNotesExpanded] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [allNotesSortBy, setAllNotesSortBy] =
    useState<SortOption>('lastModified');
  const [allNotesSortDir, setAllNotesSortDir] = useState<SortDirection>('desc');

  const setSearchInputRef = useCallback((node: HTMLInputElement | null) => {
    searchInputRef.current = node;
    if (node) {
      node.focus();
    }
  }, []);

  const recentNotes = useMemo(
    () => sortNotes(notes, 'lastModified', 'desc').slice(0, 5),
    [notes]
  );

  const forYouNotes = useMemo(
    () => getForYouNotes(notes, currentNoteId ?? null, 3),
    [notes, currentNoteId]
  );

  const filteredNotes = useMemo(
    () => (searchQuery ? filterNotes(notes, searchQuery) : []),
    [notes, searchQuery]
  );

  const allNotesSorted = useMemo(
    () => sortNotes(notes, allNotesSortBy, allNotesSortDir),
    [notes, allNotesSortBy, allNotesSortDir]
  );

  const allNotesGrouped: GroupedNotes[] = useMemo(
    () => groupNotesByDate(allNotesSorted, allNotesSortDir),
    [allNotesSorted, allNotesSortDir]
  );

  const visibleNotes = useMemo(() => {
    if (searchQuery) return filteredNotes;
    return recentNotes;
  }, [searchQuery, filteredNotes, recentNotes]);

  useEffect(() => {
    setActiveIndex(0);
  }, [searchQuery]);

  useEffect(() => {
    if (isPaletteOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
    if (!isPaletteOpen) {
      setIsAllNotesExpanded(false);
      setActiveIndex(0);
    }
  }, [isPaletteOpen]);

  const handleSelect = useCallback(
    (noteId: string) => {
      navigate(`/notes/${noteId}`);
      closePalette();
      trackNoteAccess(noteId);
    },
    [navigate, closePalette]
  );

  useEffect(() => {
    if (!isPaletteOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex((prev) => Math.min(prev + 1, visibleNotes.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' && visibleNotes[activeIndex]) {
        e.preventDefault();
        handleSelect(visibleNotes[activeIndex].id);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPaletteOpen, activeIndex, visibleNotes, handleSelect]);

  const handleBackdropClick = (e: MouseEvent) => {
    if (e.target === e.currentTarget) closePalette();
  };

  const cycleSortOption = useCallback(() => {
    const options: SortOption[] = [
      'lastModified',
      'alphabetical',
      'createdDate',
    ];
    const currentIdx = options.indexOf(allNotesSortBy);
    setAllNotesSortBy(options[(currentIdx + 1) % options.length]);
  }, [allNotesSortBy]);

  const toggleSortDir = useCallback(() => {
    setAllNotesSortDir((prev) => (prev === 'desc' ? 'asc' : 'desc'));
  }, []);

  const isSearching = searchQuery.length > 0;
  const useVirtualScroll =
    isAllNotesExpanded && allNotesSorted.length > VIRTUALIZATION_THRESHOLD;

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
              bg="white"
              borderRadius="14px"
              boxShadow="xl"
              overflow="hidden"
              zIndex={1500}
              data-testid="command-palette"
            >
              <Input
                ref={setSearchInputRef}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search notes..."
                size="lg"
                border="none"
                borderBottom="1px solid"
                borderColor="gray.200"
                borderRadius={0}
                _focus={{ borderColor: 'blue.400', boxShadow: 'none' }}
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
                      borderColor="gray.100"
                      bg="gray.50"
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
                    {filteredNotes.map((note, idx) => (
                      <PaletteNoteItem
                        key={note.id}
                        note={note}
                        isActive={idx === activeIndex}
                        searchQuery={searchQuery}
                        onSelect={handleSelect}
                      />
                    ))}
                    {filteredNotes.length === 0 && (
                      <Box px={4} py={6} textAlign="center">
                        <Text fontSize="sm" color="text.muted">
                          No notes match &ldquo;{searchQuery}&rdquo;
                        </Text>
                      </Box>
                    )}
                  </>
                )}

                {!isSearching && forYouNotes.length > 0 && (
                  <>
                    <Box
                      px={4}
                      py={1.5}
                      borderBottom="1px"
                      borderColor="gray.100"
                      bg="gray.50"
                    >
                      <Text
                        fontSize="xs"
                        fontWeight="bold"
                        color="text.muted"
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
                        isActive={false}
                        onSelect={handleSelect}
                      />
                    ))}
                  </>
                )}

                {!isSearching && (
                  <>
                    <Box
                      px={4}
                      py={1.5}
                      borderBottom="1px"
                      borderColor="gray.100"
                      bg="gray.50"
                    >
                      <Text
                        fontSize="xs"
                        fontWeight="bold"
                        color="text.muted"
                        letterSpacing="wide"
                        data-testid="recent-header"
                      >
                        RECENT
                      </Text>
                    </Box>
                    {recentNotes.map((note, idx) => (
                      <PaletteNoteItem
                        key={note.id}
                        note={note}
                        isActive={idx === activeIndex}
                        onSelect={handleSelect}
                      />
                    ))}
                  </>
                )}

                {!isSearching && (
                  <>
                    <Box
                      px={4}
                      py={2}
                      cursor="pointer"
                      borderTop="1px"
                      borderColor="gray.100"
                      _hover={{ bg: 'gray.50' }}
                      onClick={() => setIsAllNotesExpanded(!isAllNotesExpanded)}
                      data-testid="all-notes-toggle"
                    >
                      <Text fontSize="sm" color="text.secondary">
                        All Notes ({notes.length}){' '}
                        {isAllNotesExpanded ? '▾' : '▸'}
                      </Text>
                    </Box>

                    {isAllNotesExpanded && (
                      <Box data-testid="all-notes-expanded">
                        <Flex
                          px={4}
                          py={1.5}
                          gap={2}
                          bg="gray.50"
                          borderBottom="1px"
                          borderColor="gray.100"
                        >
                          <Box
                            as="button"
                            fontSize="xs"
                            color="primary.600"
                            fontWeight="medium"
                            onClick={cycleSortOption}
                            cursor="pointer"
                            _hover={{ color: 'primary.800' }}
                            data-testid="sort-option-btn"
                          >
                            {allNotesSortBy === 'lastModified'
                              ? 'Modified'
                              : allNotesSortBy === 'alphabetical'
                                ? 'A-Z'
                                : 'Created'}
                          </Box>
                          <Box
                            as="button"
                            fontSize="xs"
                            color="primary.600"
                            onClick={toggleSortDir}
                            cursor="pointer"
                            _hover={{ color: 'primary.800' }}
                            data-testid="sort-dir-btn"
                          >
                            {allNotesSortDir === 'desc' ? '↓' : '↑'}
                          </Box>
                        </Flex>

                        {useVirtualScroll ? (
                          <List
                            style={{
                              height: VIRTUAL_LIST_HEIGHT,
                              width: '100%',
                            }}
                            rowCount={allNotesSorted.length}
                            rowHeight={PALETTE_ITEM_HEIGHT}
                            rowComponent={VirtualNoteRow}
                            rowProps={{
                              notes: allNotesSorted,
                              activeIndex: -1,
                              searchQuery: '',
                              onSelect: handleSelect,
                            }}
                            data-testid="virtual-notes-list"
                          />
                        ) : (
                          allNotesGrouped.map((group) => (
                            <Box key={group.group}>
                              <Box px={4} py={1}>
                                <HStack spacing={1}>
                                  <Text
                                    fontSize="xs"
                                    fontWeight="semibold"
                                    textTransform="uppercase"
                                    letterSpacing="wide"
                                    color="text.muted"
                                  >
                                    {group.group}
                                  </Text>
                                  <Text fontSize="xs" color="text.muted">
                                    ({group.count})
                                  </Text>
                                </HStack>
                              </Box>
                              {group.notes.map((note) => (
                                <PaletteNoteItem
                                  key={note.id}
                                  note={note}
                                  isActive={false}
                                  onSelect={handleSelect}
                                />
                              ))}
                            </Box>
                          ))
                        )}
                      </Box>
                    )}
                  </>
                )}
              </VStack>

              <Box
                px={4}
                py={2}
                borderTop="1px solid"
                borderColor="gray.200"
                bg="gray.50"
              >
                <Text fontSize="xs" color="gray.600">
                  ↑↓ navigate • ↵ open • esc to close
                </Text>
              </Box>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Portal>
  );
};
