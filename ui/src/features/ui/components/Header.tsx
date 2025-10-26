import { Flex, HStack, Heading, IconButton, Image } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars } from '@fortawesome/free-solid-svg-icons';
import { UserLoginStatus } from '../../auth/components';
import Logo from '../../../../assets/images/parchmark.svg';

interface HeaderProps {
  toggleSidebar: () => void;
}

const Header = ({ toggleSidebar }: HeaderProps) => {
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
      <UserLoginStatus />
    </Flex>
  );
};

export default Header;
