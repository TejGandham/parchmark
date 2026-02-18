import {
  Flex,
  HStack,
  Heading,
  IconButton,
  Image,
  Button,
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTableList, faGear } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { UserLoginStatus } from '../../auth/components';
import { useUIStore } from '../store/ui';
import Logo from '../../../../assets/images/parchmark.svg';

const Header = () => {
  const navigate = useNavigate();
  const openPalette = useUIStore((s) => s.actions.openPalette);

  return (
    <Flex
      as="header"
      bgGradient="linear(to-r, bg.surface, primary.50, bg.surface)"
      color="primary.800"
      p={3}
      align="center"
      justify="space-between"
      borderBottom="1px solid"
      borderColor="border.default"
      boxShadow="sm"
      transition="all 0.2s"
    >
      <HStack spacing={3}>
        <Heading size="md" ml={1} fontFamily="'Playfair Display', serif">
          <Image src={Logo} alt="ParchMark Logo" h="46px" mr="10px" />
        </Heading>
      </HStack>

      <Button
        onClick={openPalette}
        variant="ghost"
        size="sm"
        leftIcon={<SearchIcon />}
        color="text.muted"
        fontWeight="normal"
        px={4}
        borderRadius="md"
        border="1px solid"
        borderColor="border.default"
        _hover={{ bg: 'bg.subtle', borderColor: 'primary.200' }}
        data-testid="palette-trigger"
      >
        Search notes… Ctrl+Shift+Space
      </Button>

      <HStack spacing={3}>
        <IconButton
          aria-label="Browse all notes"
          icon={<FontAwesomeIcon icon={faTableList} />}
          onClick={() => navigate('/notes/explore')}
          variant="ghost"
          colorScheme="primary"
          fontSize="lg"
          data-testid="explorer-link"
        />
        <IconButton
          aria-label="Settings"
          icon={<FontAwesomeIcon icon={faGear} />}
          onClick={() => navigate('/settings')}
          variant="ghost"
          colorScheme="primary"
          fontSize="lg"
          _hover={{
            transform: 'rotate(45deg)',
            transition: 'transform 0.3s ease',
          }}
        />
        <UserLoginStatus />
      </HStack>
    </Flex>
  );
};

export default Header;
