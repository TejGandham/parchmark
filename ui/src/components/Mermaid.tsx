import React, { useEffect, useRef, useState } from 'react';
import { Box, Text, Spinner, Center, useColorMode } from '@chakra-ui/react';
import { getMermaid } from '../utils/mermaidInit';

interface MermaidProps {
  chart: string;
}

let idCounter = 0;

const Mermaid: React.FC<MermaidProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { colorMode } = useColorMode();

  useEffect(() => {
    let cancelled = false;

    const renderChart = async () => {
      if (!chart.trim()) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const mermaid = await getMermaid();
        if (cancelled) return;

        mermaid.initialize({
          startOnLoad: false,
          theme: colorMode === 'dark' ? 'dark' : 'default',
          securityLevel: 'loose',
        });

        const id = `mermaid-${idCounter++}`;
        const { svg: renderedSvg } = await mermaid.render(id, chart);

        if (cancelled) return;
        setSvg(renderedSvg);
      } catch (err) {
        if (cancelled) return;
        console.error('Mermaid rendering error:', err);
        setError(
          err instanceof Error ? err.message : 'Failed to render diagram'
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    renderChart();
    return () => {
      cancelled = true;
    };
  }, [chart, colorMode]);

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
      <Box
        ref={containerRef}
        className="mermaid-diagram"
        dangerouslySetInnerHTML={svg ? { __html: svg } : undefined}
      />
    </Box>
  );
};

export default React.memo(Mermaid);
