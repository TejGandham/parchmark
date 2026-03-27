import { useCallback, useMemo } from 'react';
import { Box, Text, VStack } from '@chakra-ui/react';
import { useNavigate, useRouteLoaderData } from 'react-router-dom';
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
  searchQuery: string;
  onSelect: (id: string) => void;
}

function VirtualExplorerRow({
  index,
  style,
  notes,
  searchQuery,
  onSelect,
}: RowComponentProps<VirtualRowData>) {
  const note = notes[index];
  return (
    <Box style={style} pb={2}>
      <ExplorerNoteCard
        note={note}
        searchQuery={searchQuery || undefined}
        onSelect={onSelect}
      />
    </Box>
  );
}

export default function NotesExplorer() {
  const { notes } = useRouteLoaderData('notes-layout') as { notes: Note[] };
  const navigate = useNavigate();

  const notesSortBy = useUIStore((s) => s.notesSortBy);
  const notesSortDirection = useUIStore((s) => s.notesSortDirection);
  const notesSearchQuery = useUIStore((s) => s.notesSearchQuery);

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

  const visibleNotes = useMemo(() => {
    if (isSearching) return filteredNotes;
    const forYou = forYouNotes.length > 0 ? forYouNotes : [];
    const grouped = allNotesGrouped.flatMap((g) => g.notes);
    return [...forYou, ...grouped];
  }, [isSearching, filteredNotes, forYouNotes, allNotesGrouped]);

  const useVirtualScroll = visibleNotes.length > VIRTUALIZATION_THRESHOLD;

  const handleSelect = useCallback(
    (noteId: string) => {
      trackNoteAccess(noteId).catch(() => {});
      navigate(`/notes/${noteId}`);
    },
    [navigate]
  );

  const renderForYouSection = () => {
    if (isSearching || forYouNotes.length === 0) return null;
    return (
      <Box>
        <Text
          fontSize="xs"
          fontWeight="bold"
          color="section.forYou"
          letterSpacing="wide"
          textTransform="uppercase"
          mb={2}
          data-testid="for-you-header"
        >
          FOR YOU
        </Text>
        <VStack spacing={2} align="stretch">
          {forYouNotes.map((note) => (
            <ExplorerNoteCard
              key={`fy-${note.id}`}
              note={note}
              onSelect={handleSelect}
            />
          ))}
        </VStack>
      </Box>
    );
  };

  const renderDateGroups = () => {
    if (isSearching) return null;

    return allNotesGrouped.map((group) => {
      return (
        <Box key={group.group}>
          <Text
            fontSize="xs"
            fontWeight="bold"
            color="section.recent"
            letterSpacing="wide"
            textTransform="uppercase"
            mb={2}
          >
            {group.group} &middot; {group.notes.length}
          </Text>
          <VStack spacing={2} align="stretch">
            {group.notes.map((note) => (
              <ExplorerNoteCard
                key={note.id}
                note={note}
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
              searchQuery: notesSearchQuery,
              onSelect: handleSelect,
            }}
            data-testid="virtual-notes-list"
          />
        ) : (
          <VStack spacing={2} align="stretch">
            {filteredNotes.map((note) => (
              <ExplorerNoteCard
                key={note.id}
                note={note}
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
          No notes yet — use the + button above to create one
        </Text>
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
        <ExplorerToolbar totalNotes={notes.length} />
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
    </Box>
  );
}
