import { useCallback, useEffect, useRef, useState } from 'react';
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
import { AddIcon, SearchIcon } from '@chakra-ui/icons';
import { useUIStore } from '../../../store';
import { type SortOption } from '../../../utils/dateGrouping';

interface ExplorerToolbarProps {
  totalNotes: number;
  onCreateNote: () => void;
  isCreating: boolean;
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

export function ExplorerToolbar({
  totalNotes,
  onCreateNote,
  isCreating,
}: ExplorerToolbarProps) {
  const notesSortBy = useUIStore((s) => s.notesSortBy);
  const notesSortDirection = useUIStore((s) => s.notesSortDirection);
  const notesSearchQuery = useUIStore((s) => s.notesSearchQuery);
  const setNotesSortBy = useUIStore((s) => s.actions.setNotesSortBy);
  const toggleNotesSortDirection = useUIStore(
    (s) => s.actions.toggleNotesSortDirection
  );
  const setNotesSearchQuery = useUIStore((s) => s.actions.setNotesSearchQuery);

  const [localSearch, setLocalSearch] = useState(notesSearchQuery);
  const searchRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (notesSearchQuery === '' && localSearch !== '') {
      setLocalSearch('');
    }
  }, [notesSearchQuery, localSearch]);

  useEffect(() => {
    debounceRef.current = setTimeout(() => {
      setNotesSearchQuery(localSearch);
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [localSearch, setNotesSearchQuery]);

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setLocalSearch(e.target.value);
    },
    []
  );

  const handleSearchKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Escape') {
        setLocalSearch('');
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

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;
      if (e.key === '/') {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

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
            value={localSearch}
            onChange={handleSearchChange}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search notes…"
            size="md"
            data-testid="explorer-search"
          />
        </InputGroup>

        <HStack spacing={2}>
          <Button
            size="sm"
            variant="ghost"
            onClick={cycleSortOption}
            data-testid="explorer-sort-btn"
          >
            {SORT_LABELS[notesSortBy]}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={toggleNotesSortDirection}
            data-testid="explorer-sort-dir"
          >
            {notesSortDirection === 'desc' ? '↓' : '↑'}
          </Button>
          <Button
            size="sm"
            colorScheme="primary"
            leftIcon={<AddIcon />}
            isLoading={isCreating}
            onClick={onCreateNote}
            data-testid="explorer-create-btn"
          >
            New Note
          </Button>
        </HStack>
      </Flex>

      <Text fontSize="xs" color="text.muted" mt={2}>
        {totalNotes} notes
      </Text>
    </Box>
  );
}
