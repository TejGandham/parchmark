import React, { useCallback } from 'react';
import { Box, HStack, Text } from '@chakra-ui/react';
import { Note } from '../../../types';
import {
  getContentPreview,
  getWordCount,
  getReadingTime,
} from '../../../utils/markdownStrip';
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
        if (e.key === 'Enter') {
          e.preventDefault();
          onSelect(note.id);
        }
      },
      [onSelect, note.id],
    );

    const preview = getContentPreview(note.content);
    const wordCount = getWordCount(note.content);
    const readingTime = getReadingTime(wordCount);

    const titleContent = searchQuery
      ? highlightKeyword(note.title, searchQuery)
      : note.title;

    const previewText = preview || '';
    const previewContent = searchQuery
      ? highlightKeyword(previewText, searchQuery)
      : previewText;

    return (
      <Box
        p={4}
        borderRadius="md"
        border="1px solid"
        borderColor={isActive ? 'primary.300' : 'border.default'}
        bg={isActive ? 'primary.50' : 'bg.surface'}
        shadow="xs"
        cursor="pointer"
        transition="all 0.2s"
        _hover={{
          borderColor: 'border.emphasis',
          shadow: 'sm',
          transform: 'translateY(-1px)',
        }}
        onClick={handleSelect}
        onKeyDown={handleKeyDown}
        tabIndex={0}
        role="button"
        aria-label={`Open note: ${note.title}`}
        data-testid="explorer-note-card"
      >
        <HStack justify="space-between" align="center" mb={1}>
          <Text
            fontSize="md"
            fontWeight="semibold"
            fontFamily="'Playfair Display', serif"
            color="text.primary"
            noOfLines={1}
            flex={1}
          >
            {titleContent}
          </Text>
          <Text fontSize="xs" color="text.muted" flexShrink={0}>
            {formatCompactTime(note.updatedAt)}
          </Text>
        </HStack>

        <Text fontSize="sm" color="text.secondary" noOfLines={2} mb={2}>
          {previewContent}
        </Text>

        <HStack justify="space-between" align="center">
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
  (prevProps, nextProps) =>
    prevProps.note.id === nextProps.note.id &&
    prevProps.note.title === nextProps.note.title &&
    prevProps.note.content === nextProps.note.content &&
    prevProps.note.updatedAt === nextProps.note.updatedAt &&
    prevProps.note.createdAt === nextProps.note.createdAt &&
    prevProps.isActive === nextProps.isActive &&
    prevProps.searchQuery === nextProps.searchQuery,
);

ExplorerNoteCard.displayName = 'ExplorerNoteCard';

export default ExplorerNoteCard;
