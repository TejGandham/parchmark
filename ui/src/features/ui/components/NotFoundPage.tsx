import {
  Box,
  Flex,
  Heading,
  Text,
  Button,
  VStack,
  HStack,
  Icon,
} from '@chakra-ui/react';
import { Link } from 'react-router-dom';
import { WarningTwoIcon, ArrowBackIcon } from '@chakra-ui/icons';

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
        <VStack spacing={6} maxW="600px">
          <Box
            w="140px"
            h="140px"
            bg="primary.50"
            borderRadius="full"
            display="flex"
            alignItems="center"
            justifyContent="center"
            _dark={{
              bg: 'primary.900',
            }}
          >
            <Icon as={WarningTwoIcon} fontSize="6xl" color="primary.300" />
          </Box>

          <VStack spacing={3}>
            <Heading
              as="h1"
              size="4xl"
              color="primary.800"
              fontFamily="'Playfair Display', serif"
              _dark={{
                color: 'primary.200',
              }}
            >
              404
            </Heading>
            <Heading
              as="h2"
              size="xl"
              color="text.primary"
              fontFamily="'Playfair Display', serif"
            >
              Note Not Found
            </Heading>
            <Text fontSize="lg" color="text.secondary" maxW="400px">
              Sorry, the note you're looking for doesn't exist or may have been
              deleted.
            </Text>
          </VStack>

          <HStack spacing={4} mt={4}>
            <Link to="/notes">
              <Button
                colorScheme="primary"
                size="lg"
                leftIcon={<Icon as={ArrowBackIcon} />}
                boxShadow="md"
                _hover={{
                  transform: 'translateY(-2px)',
                  boxShadow: 'lg',
                }}
              >
                Back to Notes
              </Button>
            </Link>
          </HStack>

          <Text fontSize="sm" color="text.muted" mt={8}>
            Lost? Check your notes list or create a new one to get started.
          </Text>
        </VStack>
      </Flex>
    </Box>
  );
};

export default NotFoundPage;
