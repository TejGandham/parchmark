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
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(note.id);
    }
  };

  const handleDeleteKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      e.stopPropagation();
      onDelete(note.id);
    }
  };

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
      _focusVisible={{
        outline: '2px solid',
        outlineColor: 'primary.500',
        outlineOffset: '2px',
      }}
      onClick={() => onSelect(note.id)}
      onKeyDown={handleKeyPress}
      role="button"
      tabIndex={0}
      aria-label={`Select note: ${note.title}`}
      aria-pressed={isActive}
      className="note-transition"
      transition="all 0.2s"
    >
      <HStack justify="space-between">
        <HStack>
          <FontAwesomeIcon icon={faFile} aria-hidden="true" />
          <Text noOfLines={1}>{note.title}</Text>
        </HStack>
        <IconButton
          aria-label={`Delete note: ${note.title}`}
          icon={<FontAwesomeIcon icon={faTrash} />}
          size="xs"
          variant="ghost"
          color="text.muted"
          colorScheme="secondary"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(note.id);
          }}
          onKeyDown={handleDeleteKeyPress}
        />
      </HStack>
    </ListItem>
  );
};

export default NoteItem;
