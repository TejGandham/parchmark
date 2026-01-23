import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Box, Text, Spinner, Center } from '@chakra-ui/react';
import { getMermaid } from '../utils/mermaidInit';

interface MermaidProps {
  chart: string;
}

const Mermaid: React.FC<MermaidProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const renderDiagram = useCallback(async () => {
    if (!chart.trim()) {
      setLoading(false);
      return;
    }

    if (!containerRef.current) return;

    let cancelled = false;

    try {
      setLoading(true);
      setError(null);

      // Lazily load mermaid library
      const mermaid = await getMermaid();

      if (cancelled) return;

      // Reset the container for re-rendering
      const container = containerRef.current;
      container.removeAttribute('data-processed');

      // Use contentLoaded to process this specific element
      // This is the most reliable approach for mermaid in React
      await mermaid.contentLoaded();
    } catch (err) {
      if (cancelled) return;
      console.error('Mermaid rendering error:', err);
      setError(err instanceof Error ? err.message : 'Failed to render diagram');
    } finally {
      if (!cancelled) setLoading(false);
    }

    return () => {
      cancelled = true;
    };
  }, [chart]);

  useEffect(() => {
    renderDiagram();
  }, [renderDiagram]);

  if (error) {
    return (
      <Box
        p={4}
        bg="red.50"
        borderRadius="md"
        borderWidth="1px"
        borderColor="red.200"
      >
        <Text color="red.600" fontSize="sm">
          Diagram error: {error}
        </Text>
        <Box
          as="pre"
          mt={2}
          fontSize="xs"
          color="gray.600"
          whiteSpace="pre-wrap"
        >
          {chart}
        </Box>
      </Box>
    );
  }

  return (
    <Box position="relative">
      {loading && (
        <Center
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bg="whiteAlpha.800"
          zIndex={1}
        >
          <Spinner size="sm" color="primary.500" />
        </Center>
      )}
      <Box ref={containerRef} className="mermaid">
        {chart}
      </Box>
    </Box>
  );
};

export default React.memo(Mermaid);
