import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Box, Text, VStack, Button } from '@chakra-ui/react';
import { useNavigate, useRouteLoaderData, useFetcher } from 'react-router-dom';
import { List, type RowComponentProps } from 'react-window';
import { useUIStore } from '../../../store';
import { Note } from '../../../types';
import {
  filterNotes,
  sortNotes,
  groupNotesByDate,
  type GroupedNotes,
} from '../../../utils/dateGrouping';
import { getBlendedForYouNotes } from '../../../utils/noteScoring';
import { trackNoteAccess } from '../../../services/api';
import { VIRTUALIZATION_THRESHOLD } from '../../ui/components/commandPaletteUtils';
import ExplorerNoteCard from './ExplorerNoteCard';
import { ExplorerToolbar } from './ExplorerToolbar';

const EXPLORER_CARD_HEIGHT = 130;
const EXPLORER_VIRTUAL_HEIGHT = 600;

interface VirtualRowData {
  notes: Note[];
  activeIndex: number;
  searchQuery: string;
  onSelect: (id: string) => void;
}

function VirtualExplorerRow({
  index,
  style,
  notes,
  activeIndex,
  searchQuery,
  onSelect,
}: RowComponentProps<VirtualRowData>) {
  const note = notes[index];
  return (
    <Box style={style} pb={2}>
      <ExplorerNoteCard
        note={note}
        isActive={index === activeIndex}
        searchQuery={searchQuery || undefined}
        onSelect={onSelect}
      />
    </Box>
  );
}

export default function NotesExplorer() {
  const { notes } = useRouteLoaderData('notes-layout') as { notes: Note[] };
  const navigate = useNavigate();
  const fetcher = useFetcher<{ id: string; title: string }>();
  const createInitiatedRef = useRef(false);

  const notesSortBy = useUIStore((s) => s.notesSortBy);
  const notesSortDirection = useUIStore((s) => s.notesSortDirection);
  const notesSearchQuery = useUIStore((s) => s.notesSearchQuery);
  const setNotesSearchQuery = useUIStore((s) => s.actions.setNotesSearchQuery);

  const [activeIndex, setActiveIndex] = useState(-1);

  const filteredNotes = useMemo(
    () => filterNotes(notes, notesSearchQuery),
    [notes, notesSearchQuery]
  );

  const allNotesSorted = useMemo(
    () => sortNotes(notes, notesSortBy, notesSortDirection),
    [notes, notesSortBy, notesSortDirection]
  );

  const allNotesGrouped: GroupedNotes[] = useMemo(
    () => groupNotesByDate(allNotesSorted, notesSortDirection),
    [allNotesSorted, notesSortDirection]
  );

  const forYouNotes = useMemo(
    () => getBlendedForYouNotes(notes, null, [], 3),
    [notes]
  );

  const isSearching = notesSearchQuery.length > 0;
  const isCreating = fetcher.state !== 'idle';
  const canCreate = notesSearchQuery.length >= 4;

  const visibleNotes = useMemo(() => {
    if (isSearching) return filteredNotes;
    const forYou = forYouNotes.length > 0 ? forYouNotes : [];
    const grouped = allNotesGrouped.flatMap((g) => g.notes);
    return [...forYou, ...grouped];
  }, [isSearching, filteredNotes, forYouNotes, allNotesGrouped]);

  const useVirtualScroll = visibleNotes.length > VIRTUALIZATION_THRESHOLD;

  useEffect(() => {
    setActiveIndex(-1);
  }, [notesSearchQuery]);

  const handleSelect = useCallback(
    (noteId: string) => {
      trackNoteAccess(noteId).catch(() => {});
      navigate(`/notes/${noteId}`);
    },
    [navigate]
  );

  // CRITICAL: title field required — without it createNoteAction returns redirect instead of { id, title }
  const handleCreate = useCallback(
    (title?: string) => {
      if (isCreating) return;
      const noteTitle = title || 'New Note';
      createInitiatedRef.current = true;
      fetcher.submit(
        { content: `# ${noteTitle}\n\n`, title: noteTitle },
        { method: 'post', action: '/notes' }
      );
    },
    [fetcher, isCreating]
  );

  useEffect(() => {
    if (
      createInitiatedRef.current &&
      fetcher.state === 'idle' &&
      fetcher.data?.id
    ) {
      createInitiatedRef.current = false;
      navigate(`/notes/${fetcher.data.id}?editing=true`);
    }
  }, [fetcher.state, fetcher.data, navigate]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return;
      }

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex((prev) => Math.min(prev + 1, visibleNotes.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex((prev) => Math.max(prev - 1, 0));
      } else if (
        e.key === 'Enter' &&
        activeIndex >= 0 &&
        visibleNotes[activeIndex]
      ) {
        e.preventDefault();
        handleSelect(visibleNotes[activeIndex].id);
      } else if (e.key === 'Escape') {
        if (isSearching) {
          setNotesSearchQuery('');
        } else {
          navigate('/notes');
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    activeIndex,
    visibleNotes,
    handleSelect,
    isSearching,
    setNotesSearchQuery,
    navigate,
  ]);

  const renderForYouSection = () => {
    if (isSearching || forYouNotes.length === 0) return null;
    return (
      <Box>
        <Text
          fontSize="xs"
          fontWeight="bold"
          color="text.muted"
          letterSpacing="wide"
          textTransform="uppercase"
          mb={2}
          data-testid="for-you-header"
        >
          FOR YOU
        </Text>
        <VStack spacing={2} align="stretch">
          {forYouNotes.map((note, idx) => (
            <ExplorerNoteCard
              key={`fy-${note.id}`}
              note={note}
              isActive={idx === activeIndex}
              onSelect={handleSelect}
            />
          ))}
        </VStack>
      </Box>
    );
  };

  const renderDateGroups = () => {
    if (isSearching) return null;

    const forYouOffset = forYouNotes.length > 0 ? forYouNotes.length : 0;
    let runningIdx = forYouOffset;

    return allNotesGrouped.map((group) => {
      const startIdx = runningIdx;
      runningIdx += group.notes.length;
      return (
        <Box key={group.group}>
          <Text
            fontSize="xs"
            fontWeight="bold"
            color="text.muted"
            letterSpacing="wide"
            textTransform="uppercase"
            mb={2}
          >
            {group.group} &middot; {group.notes.length}
          </Text>
          <VStack spacing={2} align="stretch">
            {group.notes.map((note, noteIdx) => (
              <ExplorerNoteCard
                key={note.id}
                note={note}
                isActive={startIdx + noteIdx === activeIndex}
                onSelect={handleSelect}
              />
            ))}
          </VStack>
        </Box>
      );
    });
  };

  const renderSearchResults = () => {
    if (!isSearching) return null;

    return (
      <Box>
        <Text
          fontSize="xs"
          color="text.muted"
          mb={3}
          data-testid="search-result-count"
        >
          {filteredNotes.length}{' '}
          {filteredNotes.length === 1 ? 'result' : 'results'} for &ldquo;
          {notesSearchQuery}&rdquo;
        </Text>

        {useVirtualScroll ? (
          <List
            style={{ height: EXPLORER_VIRTUAL_HEIGHT, width: '100%' }}
            rowCount={filteredNotes.length}
            rowHeight={EXPLORER_CARD_HEIGHT}
            rowComponent={VirtualExplorerRow}
            rowProps={{
              notes: filteredNotes,
              activeIndex,
              searchQuery: notesSearchQuery,
              onSelect: handleSelect,
            }}
            data-testid="virtual-notes-list"
          />
        ) : (
          <VStack spacing={2} align="stretch">
            {filteredNotes.map((note, idx) => (
              <ExplorerNoteCard
                key={note.id}
                note={note}
                isActive={idx === activeIndex}
                searchQuery={notesSearchQuery}
                onSelect={handleSelect}
              />
            ))}
          </VStack>
        )}

        {filteredNotes.length === 0 && (
          <VStack spacing={3} py={8} align="center">
            <Text color="text.muted" fontSize="sm" data-testid="no-notes-found">
              No notes found
            </Text>
            {canCreate && (
              <Button
                size="sm"
                colorScheme="primary"
                variant="outline"
                isLoading={isCreating}
                onClick={() => handleCreate(notesSearchQuery)}
                data-testid="create-from-search"
              >
                Create &ldquo;{notesSearchQuery}&rdquo;
              </Button>
            )}
          </VStack>
        )}
      </Box>
    );
  };

  const renderEmptyState = () => {
    if (notes.length > 0 || isSearching) return null;
    return (
      <VStack spacing={4} py={16} align="center" data-testid="zero-notes-state">
        <Text color="text.muted" fontSize="sm">
          No notes yet
        </Text>
        <Button
          size="sm"
          colorScheme="primary"
          isLoading={isCreating}
          onClick={() => handleCreate('New Note')}
          data-testid="create-first-note-btn"
        >
          + Create your first note
        </Button>
      </VStack>
    );
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      h="100%"
      bg="bg.canvas"
      data-testid="notes-explorer"
    >
      <Box px={{ base: 4, md: 6 }} pt={4} pb={2}>
        <ExplorerToolbar
          totalNotes={notes.length}
          onCreateNote={() => handleCreate()}
          isCreating={isCreating}
        />
      </Box>

      <Box flex="1" overflowY="auto" px={{ base: 4, md: 6 }} pb={4}>
        {notes.length === 0 && !isSearching ? (
          renderEmptyState()
        ) : isSearching ? (
          renderSearchResults()
        ) : (
          <VStack spacing={6} align="stretch">
            {renderForYouSection()}
            {renderDateGroups()}
          </VStack>
        )}
      </Box>

      <Box
        px={{ base: 4, md: 6 }}
        py={2}
        borderTopWidth="1px"
        borderColor="border.default"
      >
        <Text fontSize="xs" color="text.muted">
          ↑↓ navigate · Enter open · / search · Esc back
        </Text>
      </Box>
    </Box>
  );
}
