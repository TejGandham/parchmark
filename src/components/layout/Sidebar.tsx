import { Box, Flex, Heading, IconButton, List } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus } from '@fortawesome/free-solid-svg-icons';
import { Note } from '../../types';
import { COLORS } from '../../utils/constants';
import NoteItem from '../notes/NoteItem';

interface SidebarProps {
  notes: Note[];
  currentNoteId: string;
  onSelectNote: (id: string) => void;
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
      bg={COLORS.sidebarBgColor}
      p={4}
      borderRight="1px solid"
      borderColor="rgba(88, 12, 36, 0.1)"
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
          bg="transparent"
          color={COLORS.primaryColor}
          border="1px solid"
          borderColor={COLORS.primaryLight}
          _hover={{ bg: 'rgba(88, 12, 36, 0.08)', transform: 'scale(1.05)' }}
          transition="all 0.2s"
        />
      </Flex>
      <List spacing={1}>
        {notes.map((note) => (
          <NoteItem
            key={note.id}
            note={note}
            isActive={note.id === currentNoteId}
            onSelect={onSelectNote}
            onDelete={onDeleteNote}
          />
        ))}
      </List>
    </Box>
  );
};

export default Sidebar;