import { Flex, HStack, Heading, IconButton } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars } from '@fortawesome/free-solid-svg-icons';
import { COLORS } from '../../../utils/constants';
import { UserLoginStatus } from '../../auth/components';
import Logo from '../../../../assets/images/parchmark.svg';

interface HeaderProps {
  toggleSidebar: () => void;
}

const Header = ({ toggleSidebar }: HeaderProps) => {
  return (
    <Flex
      as="header"
      bgGradient="linear(to-r, white, #f8f0f2, white)"
      color={COLORS.primaryColor}
      p={3}
      align="center"
      justify="space-between"
      borderBottom="1px solid #e2e8f0"
      boxShadow="sm"
    >
      <HStack spacing={3}>
        <IconButton
          aria-label="Toggle sidebar"
          icon={<FontAwesomeIcon icon={faBars} />}
          onClick={toggleSidebar}
          variant="ghost"
          color={COLORS.primaryColor}
          _hover={{ bg: 'rgba(88, 12, 36, 0.1)' }}
        />
        <Heading size="md" ml={1} fontFamily="'Playfair Display', serif">
          <img
            src={Logo}
            alt="ParchMark Logo"
            style={{ height: '46px', marginRight: '10px' }}
          />
        </Heading>
      </HStack>
      <UserLoginStatus />
    </Flex>
  );
};

export default Header;
