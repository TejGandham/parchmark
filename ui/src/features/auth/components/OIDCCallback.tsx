/**
 * OIDC Callback Handler Component
 * Handles the redirect from Authelia after successful authentication
 */

import { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Center, Box, Spinner, Text, VStack } from '@chakra-ui/react';
import { useAuthStore } from '../store';
import { handleError } from '../../../utils/errorHandler';

const OIDCCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { actions } = useAuthStore();
  // Prevent double execution in React StrictMode (auth code can only be used once)
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Guard against React StrictMode double-render
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const handleCallback = async () => {
      try {
        const success = await actions.handleOIDCCallbackFlow();

        if (success) {
          // Get the original location the user tried to access, or default to /notes
          const from = location.state?.from?.pathname || '/notes';
          navigate(from, { replace: true });
        } else {
          // Callback failed, redirect to login
          navigate('/login', {
            replace: true,
            state: { error: 'OIDC authentication failed' },
          });
        }
      } catch (error) {
        const appError = handleError(error);
        console.error('OIDC callback error:', appError);
        navigate('/login', {
          replace: true,
          state: { error: appError.message || 'Authentication failed' },
        });
      }
    };

    handleCallback();
  }, [navigate, location, actions]);

  return (
    <Center h="100vh">
      <VStack spacing={4}>
        <Spinner size="xl" color="purple.500" thickness="4px" />
        <Box textAlign="center">
          <Text fontSize="lg">Completing authentication...</Text>
          <Text fontSize="sm" color="gray.500" mt={2}>
            You will be redirected shortly
          </Text>
        </Box>
      </VStack>
    </Center>
  );
};

export default OIDCCallback;
