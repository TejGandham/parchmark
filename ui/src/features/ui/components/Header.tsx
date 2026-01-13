import { Flex, HStack, Heading, IconButton, Image } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars, faGear } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { UserLoginStatus } from '../../auth/components';
import Logo from '../../../../assets/images/parchmark.svg';

interface HeaderProps {
  toggleSidebar: () => void;
}

const Header = ({ toggleSidebar }: HeaderProps) => {
  const navigate = useNavigate();

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
        <IconButton
          aria-label="Toggle sidebar"
          icon={<FontAwesomeIcon icon={faBars} />}
          onClick={toggleSidebar}
          variant="ghost"
          colorScheme="primary"
        />
        <Heading size="md" ml={1} fontFamily="'Playfair Display', serif">
          <Image src={Logo} alt="ParchMark Logo" h="46px" mr="10px" />
        </Heading>
      </HStack>
      <HStack spacing={3}>
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
