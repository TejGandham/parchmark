import React, { useCallback } from 'react';
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

const NoteItem = React.memo<NoteItemProps>(
  ({ note, isActive, onSelect, onDelete }) => {
    const handleSelect = useCallback(() => {
      onSelect(note.id);
    }, [onSelect, note.id]);

    const handleDelete = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation();
        onDelete(note.id);
      },
      [onDelete, note.id]
    );

    const handleKeyPress = useCallback(
      (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(note.id);
        }
      },
      [onSelect, note.id]
    );

    const handleDeleteKeyPress = useCallback(
      (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          onDelete(note.id);
        }
      },
      [onDelete, note.id]
    );

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
        onClick={handleSelect}
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
            onClick={handleDelete}
            onKeyDown={handleDeleteKeyPress}
          />
        </HStack>
      </ListItem>
    );
  },
  // Custom comparison - only re-render if these specific props change
  (prevProps, nextProps) =>
    prevProps.note.id === nextProps.note.id &&
    prevProps.note.title === nextProps.note.title &&
    prevProps.note.updatedAt === nextProps.note.updatedAt &&
    prevProps.isActive === nextProps.isActive
);

NoteItem.displayName = 'NoteItem';

export default NoteItem;
