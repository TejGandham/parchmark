import { useState, useEffect, useRef, useCallback } from 'react';
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
import { SortOption } from '../../../utils/dateGrouping';

interface ExplorerToolbarProps {
  totalNotes: number;
  onCreateNote: () => void;
  isCreating: boolean;
}

const sortOptions: SortOption[] = [
  'lastModified',
  'alphabetical',
  'createdDate',
];

const sortLabels: Record<SortOption, string> = {
  lastModified: 'Modified',
  alphabetical: 'A-Z',
  createdDate: 'Created',
};

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
  const setNotesSearchQuery = useUIStore(
    (s) => s.actions.setNotesSearchQuery
  );

  const [localSearch, setLocalSearch] = useState(notesSearchQuery);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setNotesSearchQuery(localSearch);
    }, 300);
    return () => clearTimeout(timer);
  }, [localSearch, setNotesSearchQuery]);

  useEffect(() => {
    if (notesSearchQuery === '' && localSearch !== '') {
      setLocalSearch('');
    }
  }, [notesSearchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

  const cycleSortOption = useCallback(() => {
    const currentIdx = sortOptions.indexOf(notesSortBy);
    setNotesSortBy(sortOptions[(currentIdx + 1) % sortOptions.length]);
  }, [notesSortBy, setNotesSortBy]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === '/' &&
        !e.metaKey &&
        !e.ctrlKey &&
        document.activeElement?.tagName !== 'INPUT' &&
        document.activeElement?.tagName !== 'TEXTAREA'
      ) {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
      if (
        e.key === 'Escape' &&
        document.activeElement === searchInputRef.current
      ) {
        setLocalSearch('');
        setNotesSearchQuery('');
        searchInputRef.current?.blur();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setNotesSearchQuery]);

  return (
    <Box data-testid="explorer-toolbar">
      <Flex
        gap={3}
        align="center"
        flexDirection={{ base: 'column', md: 'row' }}
      >
        <InputGroup flex={{ base: 'auto', md: 1 }} w={{ base: '100%', md: 'auto' }}>
          <InputLeftElement pointerEvents="none">
            <SearchIcon color="text.muted" />
          </InputLeftElement>
          <Input
            ref={searchInputRef}
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            placeholder="Search notes…"
            size="md"
            pl={10}
            border="1px solid"
            borderColor="border.default"
            _focus={{ borderColor: 'primary.300', boxShadow: 'none' }}
            data-testid="explorer-search"
          />
        </InputGroup>

        <HStack spacing={2} w={{ base: '100%', md: 'auto' }} justify={{ base: 'space-between', md: 'flex-start' }}>
          <HStack spacing={1}>
            <Button
              size="sm"
              variant="ghost"
              color="text.secondary"
              onClick={cycleSortOption}
              data-testid="explorer-sort-btn"
              _hover={{ color: 'primary.800', bg: 'bg.subtle' }}
            >
              {sortLabels[notesSortBy]}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              color="text.secondary"
              onClick={toggleNotesSortDirection}
              data-testid="explorer-sort-dir"
              _hover={{ color: 'primary.800', bg: 'bg.subtle' }}
            >
              {notesSortDirection === 'desc' ? '↓' : '↑'}
            </Button>
          </HStack>

          <Button
            size="sm"
            colorScheme="primary"
            leftIcon={<AddIcon />}
            onClick={onCreateNote}
            isLoading={isCreating}
            loadingText="Creating…"
            data-testid="explorer-create-btn"
          >
            New Note
          </Button>
        </HStack>
      </Flex>

      <Text fontSize="xs" color="text.muted" mt={1}>
        {totalNotes} {totalNotes === 1 ? 'note' : 'notes'}
      </Text>
    </Box>
  );
}
