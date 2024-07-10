import { ChakraProvider } from '@chakra-ui/react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import theme from './styles/theme';
import { Box, Spinner, Center } from '@chakra-ui/react';

// Keep lazy loading only for the main route components
const NotesContainer = lazy(
  () => import('./features/notes/components/NotesContainer')
);
const NotFoundPage = lazy(
  () => import('./features/ui/components/NotFoundPage')
);

// Create a better loading fallback
const LoadingFallback = () => (
  <Center h="100vh">
    <Box textAlign="center">
      <Spinner size="xl" color="purple.500" thickness="4px" />
      <Box mt={4}>Loading...</Box>
    </Box>
  </Center>
);

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<Navigate to="/notes" replace />} />
          <Route path="/notes" element={<NotesContainer />} />
          <Route path="/notes/:noteId" element={<NotesContainer />} />
          <Route path="/not-found" element={<NotFoundPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </ChakraProvider>
  );
}

export default App;
