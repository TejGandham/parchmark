import { HStack, Text, IconButton, ListItem } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTrash, faFile } from '@fortawesome/free-solid-svg-icons';
import { Note } from '../../../types';

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
      bg={isActive ? 'primary.50' : 'transparent'}
      color={isActive ? 'primary.800' : 'text.primary'}
      _hover={{
        bg: isActive ? 'primary.100' : 'interactive.hover',
      }}
      onClick={() => onSelect(note.id)}
      className="note-transition"
      transition="all 0.2s"
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
          color="text.muted"
          colorScheme="secondary"
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
