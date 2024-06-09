import { ChakraProvider } from '@chakra-ui/react';
import NotesContainer from './features/notes/components/NotesContainer';
import theme from './styles/theme';

function App() {
  return (
    <ChakraProvider theme={theme}>
      <NotesContainer />
    </ChakraProvider>
  );
}

export default App;

