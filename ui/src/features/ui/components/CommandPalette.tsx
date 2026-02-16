import { useRef, useEffect, useCallback, type MouseEvent } from 'react';
import { Portal, Box, Input, Text, VStack } from '@chakra-ui/react';
import { AnimatePresence, motion } from 'framer-motion';
import { useUIStore } from '../store/ui';

export const CommandPalette = () => {
  const isPaletteOpen = useUIStore((state) => state.isPaletteOpen);
  const closePalette = useUIStore((state) => state.actions.closePalette);
  const searchQuery = useUIStore((state) => state.paletteSearchQuery);
  const setSearchQuery = useUIStore(
    (state) => state.actions.setPaletteSearchQuery
  );
  const searchInputRef = useRef<HTMLInputElement>(null);

  const setSearchInputRef = useCallback((node: HTMLInputElement | null) => {
    searchInputRef.current = node;
    if (node) {
      node.focus();
    }
  }, []);

  useEffect(() => {
    if (isPaletteOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isPaletteOpen]);

  const handleBackdropClick = (e: MouseEvent) => {
    if (e.target === e.currentTarget) closePalette();
  };

  return (
    <Portal>
      <AnimatePresence>
        {isPaletteOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            <Box
              position="fixed"
              top={0}
              left={0}
              right={0}
              bottom={0}
              bg="blackAlpha.600"
              backdropFilter="blur(4px)"
              zIndex={1400}
              onClick={handleBackdropClick}
              data-testid="command-palette-backdrop"
            />

            <Box
              role="dialog"
              aria-label="Command palette"
              position="fixed"
              top="15vh"
              left="50%"
              transform="translateX(-50%)"
              width={{ base: '90vw', md: '520px' }}
              maxHeight="60vh"
              bg="white"
              borderRadius="14px"
              boxShadow="xl"
              overflow="hidden"
              zIndex={1500}
              data-testid="command-palette"
            >
              <Input
                ref={setSearchInputRef}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search notes..."
                size="lg"
                border="none"
                borderBottom="1px solid"
                borderColor="gray.200"
                borderRadius={0}
                _focus={{ borderColor: 'blue.400', boxShadow: 'none' }}
                data-testid="command-palette-search"
              />

              <VStack
                spacing={0}
                align="stretch"
                overflowY="auto"
                maxHeight="50vh"
              >
                {/* TODO Task 4: Add "Recent", "All Notes" sections */}
                {/* TODO Task 5: Add "For You" section */}
              </VStack>

              <Box
                px={4}
                py={2}
                borderTop="1px solid"
                borderColor="gray.200"
                bg="gray.50"
              >
                <Text fontSize="xs" color="gray.600">
                  ↑↓ navigate • ↵ open • esc to close
                </Text>
              </Box>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Portal>
  );
};
