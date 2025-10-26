import { Box, Flex, Heading, IconButton, List } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus } from '@fortawesome/free-solid-svg-icons';
import { Note } from '../../../types';
import NoteItem from '../../notes/components/NoteItem';

interface SidebarProps {
  notes: Note[];
  currentNoteId: string;
  onSelectNote: (id: string | null) => void;
  onCreateNote: () => void;
  onDeleteNote: (id: string) => void;
}

const Sidebar = ({
  notes,
  currentNoteId,
  onSelectNote,
  onCreateNote,
  onDeleteNote,
}: SidebarProps) => {
  return (
    <Box
      w="250px"
      bg="bg.surface"
      p={4}
      borderRight="1px solid"
      borderColor="border.default"
      overflowY="auto"
      className="sidebar-shadow"
    >
      <Flex justify="space-between" mb={4}>
        <Heading size="sm" fontFamily="'Playfair Display', serif">
          Notes
        </Heading>
        <IconButton
          aria-label="Create new note"
          icon={<FontAwesomeIcon icon={faPlus} />}
          size="sm"
          onClick={onCreateNote}
          variant="ghost"
          colorScheme="primary"
          _hover={{ transform: 'scale(1.05)' }}
        />
      </Flex>
      <List spacing={1}>
        {Array.isArray(notes) && notes.length > 0 ? (
          notes.map((note) => (
            <NoteItem
              key={note.id}
              note={note}
              isActive={note.id === currentNoteId}
              onSelect={onSelectNote}
              onDelete={onDeleteNote}
            />
          ))
        ) : (
          <Box p={2} textAlign="center" color="text.muted" fontSize="sm">
            No notes yet
          </Box>
        )}
      </List>
    </Box>
  );
};

export default Sidebar;
