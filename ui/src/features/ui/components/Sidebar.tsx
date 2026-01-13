import React from 'react';
import {
  Box,
  Flex,
  Heading,
  IconButton,
  List,
  VStack,
  Text,
  Icon,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  HStack,
} from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus, faSort } from '@fortawesome/free-solid-svg-icons';
import { AddIcon, SearchIcon, ChevronDownIcon } from '@chakra-ui/icons';
import { motion } from 'framer-motion';
import { Note } from '../../../types';
import NoteItem from '../../notes/components/NoteItem';
import { NoteListSkeleton } from '../../../components/NoteCardSkeleton';
import {
  sortNotes,
  filterNotes,
  groupNotesByDate,
  SortOption,
} from '../../../utils/dateGrouping';
import { useUIStore } from '../store';

interface SidebarProps {
  notes: Note[];
  currentNoteId: string;
  onSelectNote: (id: string | null) => void;
  onCreateNote: () => void;
  onDeleteNote: (id: string) => void;
  isLoading?: boolean;
}

const MotionList = motion(List);
const MotionBox = motion(Box);

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'lastModified', label: 'Last Modified' },
  { value: 'alphabetical', label: 'Alphabetical' },
  { value: 'createdDate', label: 'Created Date' },
];

const Sidebar = ({
  notes,
  currentNoteId,
  onSelectNote,
  onCreateNote,
  onDeleteNote,
  isLoading = false,
}: SidebarProps) => {
  const notesSortBy = useUIStore((state) => state.notesSortBy);
  const notesSearchQuery = useUIStore((state) => state.notesSearchQuery);
  const notesGroupByDate = useUIStore((state) => state.notesGroupByDate);
  const { setNotesSortBy, setNotesSearchQuery } = useUIStore(
    (state) => state.actions
  );

  // Process notes: filter, sort, and group
  const processedNotes = React.useMemo(() => {
    let result = filterNotes(notes, notesSearchQuery);
    result = sortNotes(result, notesSortBy);
    return result;
  }, [notes, notesSearchQuery, notesSortBy]);

  const groupedNotes = React.useMemo(() => {
    if (notesGroupByDate) {
      return groupNotesByDate(processedNotes);
    }
    return null;
  }, [processedNotes, notesGroupByDate]);

  const currentSortLabel =
    sortOptions.find((opt) => opt.value === notesSortBy)?.label ||
    'Last Modified';

  return (
    <Box
      w="280px"
      h="100%"
      bg="bg.surface"
      borderRight="1px solid"
      borderColor="border.default"
      display="flex"
      flexDirection="column"
      className="sidebar-shadow"
    >
      {/* Header */}
      <Flex
        justify="space-between"
        align="center"
        px={4}
        py={3}
        borderBottom="1px solid"
        borderColor="border.default"
        bg="bg.subtle"
      >
        <Heading size="sm" fontFamily="'Playfair Display', serif">
          Notes
        </Heading>
        <IconButton
          aria-label="Create new note"
          icon={<FontAwesomeIcon icon={faPlus} />}
          size="sm"
          onClick={onCreateNote}
          colorScheme="primary"
          bgGradient="linear(to-r, primary.800, primary.600)"
          color="white"
          boxShadow="sm"
          _hover={{
            transform: 'scale(1.05)',
            boxShadow: 'md',
          }}
        />
      </Flex>

      {/* Search Bar */}
      <Box px={4} pt={3} pb={2}>
        <InputGroup size="sm">
          <InputLeftElement pointerEvents="none">
            <Icon as={SearchIcon} color="text.muted" boxSize={3} />
          </InputLeftElement>
          <Input
            placeholder="Search notes..."
            value={notesSearchQuery}
            onChange={(e) => setNotesSearchQuery(e.target.value)}
            bg="bg.subtle"
            borderColor="border.default"
            _focus={{
              bg: 'bg.surface',
              borderColor: 'primary.500',
              boxShadow: '0 0 0 1px var(--chakra-colors-primary-500)',
            }}
          />
        </InputGroup>
      </Box>

      {/* Sorting Dropdown */}
      <Box px={4} pb={3}>
        <Menu>
          <MenuButton
            as={Button}
            size="sm"
            variant="ghost"
            rightIcon={<Icon as={ChevronDownIcon} boxSize={3} />}
            leftIcon={<FontAwesomeIcon icon={faSort} size="sm" />}
            width="100%"
            justifyContent="space-between"
            fontWeight="normal"
            fontSize="sm"
            color="text.secondary"
          >
            {currentSortLabel}
          </MenuButton>
          <MenuList fontSize="sm">
            {sortOptions.map((option) => (
              <MenuItem
                key={option.value}
                onClick={() => setNotesSortBy(option.value)}
                fontWeight={
                  notesSortBy === option.value ? 'semibold' : 'normal'
                }
                color={
                  notesSortBy === option.value ? 'primary.600' : 'text.primary'
                }
              >
                {option.label}
              </MenuItem>
            ))}
          </MenuList>
        </Menu>
      </Box>

      {/* Notes List */}
      <Box flex="1" overflowY="auto" px={4} pb={4}>
        {isLoading ? (
          <NoteListSkeleton />
        ) : Array.isArray(notes) && notes.length > 0 ? (
          notesGroupByDate && groupedNotes ? (
            // Grouped by date
            <VStack align="stretch" spacing={4}>
              {groupedNotes.map((group) => (
                <MotionBox
                  key={group.group}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <HStack mb={2} spacing={2}>
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
                  <MotionList
                    spacing={1}
                    initial="hidden"
                    animate="visible"
                    variants={{
                      visible: {
                        transition: {
                          staggerChildren: 0.05,
                        },
                      },
                    }}
                  >
                    {group.notes.map((note) => (
                      <MotionBox
                        key={note.id}
                        variants={{
                          hidden: { opacity: 0, x: -10 },
                          visible: { opacity: 1, x: 0 },
                        }}
                        transition={{ duration: 0.2 }}
                      >
                        <NoteItem
                          note={note}
                          isActive={note.id === currentNoteId}
                          onSelect={onSelectNote}
                          onDelete={onDeleteNote}
                        />
                      </MotionBox>
                    ))}
                  </MotionList>
                </MotionBox>
              ))}
            </VStack>
          ) : (
            // Not grouped - simple list with stagger
            <MotionList
              spacing={1}
              initial="hidden"
              animate="visible"
              variants={{
                visible: {
                  transition: {
                    staggerChildren: 0.05,
                  },
                },
              }}
            >
              {processedNotes.map((note) => (
                <MotionBox
                  key={note.id}
                  variants={{
                    hidden: { opacity: 0, x: -10 },
                    visible: { opacity: 1, x: 0 },
                  }}
                  transition={{ duration: 0.2 }}
                >
                  <NoteItem
                    note={note}
                    isActive={note.id === currentNoteId}
                    onSelect={onSelectNote}
                    onDelete={onDeleteNote}
                  />
                </MotionBox>
              ))}
            </MotionList>
          )
        ) : (
          <VStack spacing={4} py={8} px={2}>
            <Box
              w="60px"
              h="60px"
              bg="primary.50"
              borderRadius="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              <Icon as={AddIcon} fontSize="2xl" color="primary.600" />
            </Box>
            <VStack spacing={2}>
              <Heading
                size="sm"
                color="text.primary"
                fontFamily="'Playfair Display', serif"
                textAlign="center"
              >
                No notes yet
              </Heading>
              <Text
                fontSize="xs"
                color="text.muted"
                textAlign="center"
                maxW="180px"
              >
                Start capturing your thoughts and ideas
              </Text>
            </VStack>
            <Button
              size="sm"
              colorScheme="primary"
              onClick={onCreateNote}
              leftIcon={<Icon as={AddIcon} />}
              boxShadow="sm"
              _hover={{
                transform: 'translateY(-2px)',
                boxShadow: 'md',
              }}
            >
              Create Note
            </Button>
          </VStack>
        )}
      </Box>
    </Box>
  );
};

export default Sidebar;
