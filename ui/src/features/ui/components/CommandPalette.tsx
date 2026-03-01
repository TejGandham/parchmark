import {
  useRef,
  useEffect,
  useCallback,
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
  Flex,
  Skeleton,
  Button,
} from '@chakra-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  useNavigate,
  useParams,
  useFetcher,
  useNavigation,
} from 'react-router-dom';
import { List, type RowComponentProps } from 'react-window';
import { useUIStore } from '../store/ui';
import { Note, SimilarNote } from '../../../types';
import {
  filterNotes,
  sortNotes,
  groupNotesByDate,
  type SortOption,
  type SortDirection,
  type GroupedNotes,
} from '../../../utils/dateGrouping';
import { formatCompactTime } from '../../../utils/compactTime';
import { getBlendedForYouNotes } from '../../../utils/noteScoring';
import { trackNoteAccess, getSimilarNotes } from '../../../services/api';
import {
  VIRTUALIZATION_THRESHOLD,
  PALETTE_ITEM_HEIGHT,
  VIRTUAL_LIST_HEIGHT,
  highlightKeyword,
} from './commandPaletteUtils';

interface CommandPaletteProps {
  notes?: Note[];
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
  const fetcher = useFetcher<{ id: string; title: string }>();
  const navigation = useNavigation();
  const isRouteLoading = navigation.state === 'loading';
  const createInitiatedRef = useRef(false);

  const [isAllNotesExpanded, setIsAllNotesExpanded] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [allNotesSortBy, setAllNotesSortBy] =
    useState<SortOption>('lastModified');
  const [allNotesSortDir, setAllNotesSortDir] = useState<SortDirection>('desc');
  const [similarNotes, setSimilarNotes] = useState<SimilarNote[]>([]);

  const setSearchInputRef = useCallback((node: HTMLInputElement | null) => {
    searchInputRef.current = node;
    if (node) {
      node.focus();
    }
  }, []);

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

  const isSearching = searchQuery.length > 0;
  const hasResults = filteredNotes.length > 0;
  const canCreate = searchQuery.length >= 4;
  const isCreating =
    fetcher.state === 'submitting' || fetcher.state === 'loading';

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

  const handleCreate = useCallback(
    (title?: string) => {
      if (isCreating) return;
      const noteTitle = title || searchQuery;
      createInitiatedRef.current = true;
      fetcher.submit(
        { content: `# ${noteTitle}\n\n`, title: noteTitle },
        { method: 'post', action: '/notes' }
      );
    },
    [fetcher, searchQuery, isCreating]
  );

  useEffect(() => {
    if (
      createInitiatedRef.current &&
      fetcher.state === 'idle' &&
      fetcher.data?.id
    ) {
      createInitiatedRef.current = false;
      navigate(`/notes/${fetcher.data.id}?editing=true`);
      closePalette();
    }
  }, [fetcher.state, fetcher.data, navigate, closePalette]);

  useEffect(() => {
    if (!isPaletteOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        closePalette();
        return;
      }

      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        if (isSearching && !hasResults && canCreate) {
          e.preventDefault();
          handleCreate();
        }
        return;
      }

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
  }, [
    isPaletteOpen,
    closePalette,
    activeIndex,
    visibleNotes,
    handleSelect,
    isSearching,
    hasResults,
    canCreate,
    handleCreate,
  ]);

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
                {isRouteLoading && (
                  <>
                    <Box
                      px={4}
                      py={1.5}
                      bg="gray.50"
                      borderBottom="1px"
                      borderColor="gray.100"
                    >
                      <Skeleton height="12px" width="60px" />
                    </Box>
                    {[...Array(3)].map((_, i) => (
                      <HStack
                        key={i}
                        px={4}
                        py={2}
                        spacing={3}
                        data-testid="skeleton-item"
                      >
                        <Skeleton height="16px" flex={1} />
                        <Skeleton height="12px" width="30px" />
                      </HStack>
                    ))}
                  </>
                )}

                {!isRouteLoading && isSearching && (
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
                      <>
                        <Box px={4} py={3} textAlign="center">
                          <Text
                            fontSize="sm"
                            color="text.muted"
                            data-testid="no-notes-found"
                          >
                            No notes found
                          </Text>
                        </Box>
                        <Box
                          px={4}
                          py={3}
                          cursor={canCreate ? 'pointer' : 'not-allowed'}
                          opacity={canCreate ? 1 : 0.5}
                          _hover={canCreate ? { bg: 'red.50' } : {}}
                          onClick={() => canCreate && handleCreate()}
                          data-testid="create-from-search"
                        >
                          <Text
                            color={canCreate ? 'red.700' : 'text.muted'}
                            fontWeight="medium"
                            fontSize="sm"
                          >
                            {isCreating
                              ? 'Creating...'
                              : `Create "${searchQuery}"`}
                          </Text>
                          {!canCreate && (
                            <Text fontSize="xs" color="text.muted" mt={1}>
                              Minimum 4 characters required
                            </Text>
                          )}
                        </Box>
                      </>
                    )}
                  </>
                )}

                {!isRouteLoading && !isSearching && notes.length === 0 && (
                  <VStack
                    spacing={4}
                    p={8}
                    align="center"
                    data-testid="zero-notes-state"
                  >
                    <Text color="text.muted" fontSize="sm">
                      No notes yet
                    </Text>
                    <Button
                      size="sm"
                      colorScheme="red"
                      variant="solid"
                      isLoading={isCreating}
                      onClick={() => handleCreate('New Note')}
                      data-testid="create-first-note-btn"
                    >
                      Create your first note
                    </Button>
                  </VStack>
                )}

                {!isRouteLoading && !isSearching && forYouNotes.length > 0 && (
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

                {!isRouteLoading && !isSearching && notes.length > 0 && (
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

                {!isRouteLoading && !isSearching && notes.length > 0 && (
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

              {!isSearching && notes.length > 0 && (
                <Box
                  px={4}
                  py={2}
                  borderTop="1px solid"
                  borderColor="gray.100"
                  cursor="pointer"
                  _hover={{ bg: 'gray.50' }}
                  onClick={() => {
                    navigate('/notes/explore');
                    closePalette();
                  }}
                  data-testid="browse-all-link"
                >
                  <Text fontSize="sm" color="primary.600">
                    Browse All Notes →
                  </Text>
                </Box>
              )}

              <Box
                px={4}
                py={2}
                borderTop="1px solid"
                borderColor="gray.200"
                bg="gray.50"
              >
                <Text fontSize="xs" color="gray.600">
                  {`↑↓ navigate • ↵ open${isSearching && !hasResults && canCreate ? ' • ⌘↵ create' : ''} • esc to close`}
                </Text>
              </Box>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Portal>
  );
};
