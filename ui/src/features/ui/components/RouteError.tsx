// ui/src/features/ui/components/RouteError.tsx
import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom';
import { Heading, Text, Button, Center, VStack } from '@chakra-ui/react';

export default function RouteError() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    if (error.status === 401) {
      return (
        <Center h="100vh" bg="bg.canvas">
          <VStack spacing={4}>
            <Heading size="lg" fontFamily="'Playfair Display', serif">
              Session Expired
            </Heading>
            <Text color="text.muted">Please log in again to continue.</Text>
            <Button as={Link} to="/login" colorScheme="primary">
              Log In
            </Button>
          </VStack>
        </Center>
      );
    }

    return (
      <Center h="100vh" bg="bg.canvas">
        <VStack spacing={4}>
          <Heading size="2xl" color="text.muted">
            {error.status}
          </Heading>
          <Text fontSize="lg" color="text.secondary">
            {error.statusText}
          </Text>
          <Button as={Link} to="/notes" colorScheme="primary" mt={4}>
            Back to Notes
          </Button>
        </VStack>
      </Center>
    );
  }

  return (
    <Center h="100vh" bg="bg.canvas">
      <VStack spacing={4}>
        <Heading size="lg" fontFamily="'Playfair Display', serif">
          Something went wrong
        </Heading>
        <Text color="text.muted">
          {error instanceof Error ? error.message : 'Unknown error'}
        </Text>
        <Button as={Link} to="/notes" colorScheme="primary" mt={4}>
          Back to Notes
        </Button>
      </VStack>
    </Center>
  );
}
