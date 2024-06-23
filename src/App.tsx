import { ChakraProvider } from '@chakra-ui/react';
import { Routes, Route, Navigate } from 'react-router-dom';
import NotesContainer from './features/notes/components/NotesContainer';
import NotFoundPage from './components/common/NotFoundPage';
import theme from './styles/theme';

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Routes>
        <Route path="/" element={<Navigate to="/notes" replace />} />
        <Route path="/notes" element={<NotesContainer />} />
        <Route path="/notes/:noteId" element={<NotesContainer />} />
        <Route path="/not-found" element={<NotFoundPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </ChakraProvider>
  );
}

export default App;
