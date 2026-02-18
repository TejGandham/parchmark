import React, { useCallback } from 'react';
import { Box, Text, HStack } from '@chakra-ui/react';
import { Note } from '../../../types';
import { getContentPreview, getWordCount, getReadingTime } from '../../../utils/markdownStrip';
import { formatCompactTime } from '../../../utils/compactTime';
import { highlightKeyword } from '../../ui/components/commandPaletteUtils';

interface ExplorerNoteCardProps {
  note: Note;
  isActive: boolean;
  searchQuery?: string;
  onSelect: (id: string) => void;
}

const ExplorerNoteCard = React.memo<ExplorerNoteCardProps>(
  ({ note, isActive, searchQuery, onSelect }) => {
    const handleSelect = useCallback(() => {
      onSelect(note.id);
    }, [onSelect, note.id]);

    const handleKeyDown = useCallback(
      (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(note.id);
        }
      },
      [onSelect, note.id]
    );

    const preview = getContentPreview(note.content, 120);
    const wordCount = getWordCount(note.content);
    const readingTime = getReadingTime(wordCount);

    return (
      <Box
        p={4}
        borderRadius="md"
        cursor="pointer"
        bg={isActive ? 'primary.50' : 'bg.surface'}
        borderWidth="1px"
        borderColor={isActive ? 'primary.300' : 'border.default'}
        boxShadow="xs"
        transition="all 0.2s"
        _hover={{
          borderColor: 'border.emphasis',
          boxShadow: 'sm',
          transform: 'translateY(-1px)',
        }}
        _focusVisible={{
          outline: '2px solid',
          outlineColor: 'primary.500',
          outlineOffset: '2px',
        }}
        onClick={handleSelect}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-label={`Open note: ${note.title}`}
        data-testid="explorer-note-card"
      >
        <HStack justify="space-between">
          <Text
            fontFamily="'Playfair Display', serif"
            fontSize="md"
            fontWeight="semibold"
            noOfLines={1}
            color="text.primary"
            flex={1}
          >
            {searchQuery ? highlightKeyword(note.title, searchQuery) : note.title}
          </Text>
          <Text fontSize="xs" color="text.muted" flexShrink={0} ml={2}>
            {formatCompactTime(note.updatedAt)}
          </Text>
        </HStack>

        <Text fontSize="sm" color="text.secondary" noOfLines={2} mt={1}>
          {searchQuery ? highlightKeyword(preview, searchQuery) : preview}
        </Text>

        <HStack justify="space-between" mt={1}>
          <Text fontSize="xs" color="text.muted">
            {wordCount} words &middot; {readingTime} min read
          </Text>
          <Text fontSize="xs" color="text.muted">
            {formatCompactTime(note.createdAt)}
          </Text>
        </HStack>
      </Box>
    );
  },
  (prev, next) =>
    prev.note.id === next.note.id &&
    prev.note.title === next.note.title &&
    prev.note.content === next.note.content &&
    prev.note.updatedAt === next.note.updatedAt &&
    prev.note.createdAt === next.note.createdAt &&
    prev.isActive === next.isActive &&
    prev.searchQuery === next.searchQuery
);

ExplorerNoteCard.displayName = 'ExplorerNoteCard';

export default ExplorerNoteCard;
