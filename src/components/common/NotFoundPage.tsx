import { Box, Flex, Heading, Text, Button } from '@chakra-ui/react';
import { Link } from 'react-router-dom';
import { COLORS } from '../../utils/constants';
import { colors } from '../../styles/tokens';

const NotFoundPage = () => {
  return (
    <Box minH="100vh" bg={COLORS.bgColor} className="bg-texture">
      <Flex
        height="100vh"
        alignItems="center"
        justifyContent="center"
        direction="column"
        p={8}
        textAlign="center"
      >
        <Heading as="h1" size="2xl" mb={4} color={COLORS.headingColor}>
          404
        </Heading>
        <Heading as="h2" size="xl" mb={6} color={COLORS.headingColor}>
          Note Not Found
        </Heading>
        <Text fontSize="lg" mb={8} color={COLORS.textColor}>
          Sorry, the note you're looking for doesn't exist or may have been
          deleted.
        </Text>
        <Link to="/notes">
          <Button
            bg={colors.primary.main}
            color="white"
            size="lg"
            _hover={{ bg: colors.primary.light }}
            _active={{ bg: colors.primary.dark }}
          >
            Back to Notes
          </Button>
        </Link>
      </Flex>
    </Box>
  );
};

export default NotFoundPage;
