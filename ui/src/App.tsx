// ui/src/App.tsx
import { ChakraProvider } from '@chakra-ui/react';
import { RouterProvider } from 'react-router-dom';
import theme from './styles/theme';
import { router } from './router';
import { useTokenExpirationMonitor } from './features/auth/hooks/useTokenExpirationMonitor';

function App() {
  // Monitor JWT token expiration
  useTokenExpirationMonitor();

  return (
    <ChakraProvider theme={theme}>
      <RouterProvider router={router} />
    </ChakraProvider>
  );
}

export default App;
