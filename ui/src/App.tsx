import { ChakraProvider } from '@chakra-ui/react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import theme from './styles/theme';
import { Box, Spinner, Center } from '@chakra-ui/react';
import ProtectedRoute from './features/auth/components/ProtectedRoute';
import { useAuthStore } from './features/auth/store';
import { useTokenExpirationMonitor } from './features/auth/hooks/useTokenExpirationMonitor';

// Keep lazy loading only for the main route components
const NotesContainer = lazy(
  () => import('./features/notes/components/NotesContainer')
);
const NotFoundPage = lazy(
  () => import('./features/ui/components/NotFoundPage')
);
const LoginForm = lazy(() => import('./features/auth/components/LoginForm'));
const OIDCCallback = lazy(
  () => import('./features/auth/components/OIDCCallback')
);
const Settings = lazy(() => import('./features/settings/components/Settings'));

// Create a better loading fallback
const LoadingFallback = () => (
  <Center h="100vh">
    <Box textAlign="center">
      <Spinner size="xl" color="purple.500" thickness="4px" />
      <Box mt={4}>Loading...</Box>
    </Box>
  </Center>
);

const RootRoute = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return <Navigate to={isAuthenticated ? '/notes' : '/login'} replace />;
};

function App() {
  // Monitor JWT token expiration
  useTokenExpirationMonitor();

  return (
    <ChakraProvider theme={theme}>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<RootRoute />} />
          <Route path="/login" element={<LoginForm />} />
          <Route path="/oidc/callback" element={<OIDCCallback />} />
          <Route
            path="/notes"
            element={
              <ProtectedRoute>
                <NotesContainer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notes/:noteId"
            element={
              <ProtectedRoute>
                <NotesContainer />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route path="/not-found" element={<NotFoundPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </ChakraProvider>
  );
}

export default App;
