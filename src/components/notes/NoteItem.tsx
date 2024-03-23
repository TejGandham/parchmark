import { HStack, Text, IconButton, ListItem } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faFile } from '@fortawesome/free-solid-svg-icons';
import { Note } from '../../types';
import { COLORS } from '../../utils/constants';

interface NoteItemProps {
  note: Note;
  isActive: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

const NoteItem = ({ note, isActive, onSelect, onDelete }: NoteItemProps) => {
  return (
    <ListItem
      key={note.id}
      p={2}
      borderRadius="md"
      cursor="pointer"
      bg={isActive ? 'rgba(88, 12, 36, 0.08)' : 'transparent'}
      color={isActive ? COLORS.primaryColor : 'inherit'}
      _hover={{
        bg: isActive ? 'rgba(88, 12, 36, 0.12)' : 'gray.100',
      }}
      onClick={() => onSelect(note.id)}
      className="note-transition"
    >
      <HStack justify="space-between">
        <HStack>
          <FontAwesomeIcon icon={faFile} />
          <Text noOfLines={1}>{note.title}</Text>
        </HStack>
        <IconButton
          aria-label="Delete note"
          icon={<FontAwesomeIcon icon={faTrash} />}
          size="xs"
          variant="ghost"
          color="gray.500"
          _hover={{ color: COLORS.complementaryColor }}
          onClick={(e) => {
            e.stopPropagation();
            onDelete(note.id);
          }}
        />
      </HStack>
    </ListItem>
  );
};

export default NoteItem;