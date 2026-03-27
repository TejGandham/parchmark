import { useCallback, useRef } from 'react';
import {
  Box,
  Button,
  Flex,
  HStack,
  Input,
  InputGroup,
  InputLeftElement,
  Text,
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import { useUIStore } from '../../../store';
import { type SortOption } from '../../../utils/dateGrouping';

interface ExplorerToolbarProps {
  totalNotes: number;
}

const SORT_LABELS: Record<SortOption, string> = {
  lastModified: 'Modified',
  alphabetical: 'A-Z',
  createdDate: 'Created',
};

const SORT_OPTIONS: SortOption[] = [
  'lastModified',
  'alphabetical',
  'createdDate',
];

export function ExplorerToolbar({ totalNotes }: ExplorerToolbarProps) {
  const notesSortBy = useUIStore((s) => s.notesSortBy);
  const notesSortDirection = useUIStore((s) => s.notesSortDirection);
  const notesSearchQuery = useUIStore((s) => s.notesSearchQuery);
  const setNotesSortBy = useUIStore((s) => s.actions.setNotesSortBy);
  const toggleNotesSortDirection = useUIStore(
    (s) => s.actions.toggleNotesSortDirection
  );
  const setNotesSearchQuery = useUIStore((s) => s.actions.setNotesSearchQuery);

  const searchRef = useRef<HTMLInputElement>(null);

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setNotesSearchQuery(e.target.value);
    },
    [setNotesSearchQuery]
  );

  const handleSearchKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Escape') {
        setNotesSearchQuery('');
        searchRef.current?.blur();
      }
    },
    [setNotesSearchQuery]
  );

  const cycleSortOption = useCallback(() => {
    const currentIdx = SORT_OPTIONS.indexOf(notesSortBy);
    setNotesSortBy(SORT_OPTIONS[(currentIdx + 1) % SORT_OPTIONS.length]);
  }, [notesSortBy, setNotesSortBy]);

  return (
    <Box>
      <Flex
        flexDirection={{ base: 'column', md: 'row' }}
        gap={3}
        align={{ base: 'stretch', md: 'center' }}
      >
        <InputGroup flex={1}>
          <InputLeftElement pointerEvents="none">
            <SearchIcon color="text.muted" />
          </InputLeftElement>
          <Input
            ref={searchRef}
            value={notesSearchQuery}
            onChange={handleSearchChange}
            onKeyDown={handleSearchKeyDown}
            placeholder="Filter notes..."
            size="md"
            data-testid="explorer-search"
          />
        </InputGroup>

        <HStack spacing={2}>
          <Button
            size="sm"
            variant="ghost"
            onClick={cycleSortOption}
            color="text.secondary"
            _hover={{ bg: 'primary.50', color: 'primary.800' }}
            data-testid="explorer-sort-btn"
          >
            {SORT_LABELS[notesSortBy]}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={toggleNotesSortDirection}
            color="text.secondary"
            _hover={{ bg: 'primary.50', color: 'primary.800' }}
            data-testid="explorer-sort-dir"
          >
            {notesSortDirection === 'desc' ? '↓' : '↑'}
          </Button>
        </HStack>
      </Flex>

      <Text fontSize="xs" color="text.muted" mt={2}>
        {totalNotes} notes
      </Text>
    </Box>
  );
}
