// Skeleton loading component for note cards
// Provides visual feedback while notes are being loaded

import { Box, Skeleton, VStack, HStack } from '@chakra-ui/react';

const NoteCardSkeleton = () => {
  return (
    <Box p={2} borderRadius="md" bg="bg.surface" mb={1}>
      <HStack justify="space-between">
        <HStack spacing={2} flex="1">
          <Skeleton w="12px" h="12px" />
          <Skeleton h="16px" flex="1" />
        </HStack>
        <Skeleton w="24px" h="24px" />
      </HStack>
    </Box>
  );
};

export const NoteListSkeleton = () => {
  return (
    <VStack spacing={1} align="stretch">
      {[...Array(5)].map((_, i) => (
        <NoteCardSkeleton key={i} />
      ))}
    </VStack>
  );
};

export default NoteCardSkeleton;
