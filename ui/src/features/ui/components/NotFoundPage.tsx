import { Box, Flex, Heading, Text, Button } from '@chakra-ui/react';
import { Link } from 'react-router-dom';

const NotFoundPage = () => {
  return (
    <Box minH="100vh" bg="bg.canvas" className="bg-texture">
      <Flex
        height="100vh"
        alignItems="center"
        justifyContent="center"
        direction="column"
        p={8}
        textAlign="center"
      >
        <Heading as="h1" size="2xl" mb={4} textStyle="display">
          404
        </Heading>
        <Heading as="h2" size="xl" mb={6} textStyle="h1">
          Note Not Found
        </Heading>
        <Text fontSize="lg" mb={8} textStyle="body">
          Sorry, the note you're looking for doesn't exist or may have been
          deleted.
        </Text>
        <Link to="/notes">
          <Button colorScheme="primary" size="lg">
            Back to Notes
          </Button>
        </Link>
      </Flex>
    </Box>
  );
};

export default NotFoundPage;
