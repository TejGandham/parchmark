import React from 'react';
import {
  Box,
  VStack,
  Text,
  Divider,
  useBreakpointValue,
} from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faUser,
  faCog,
  faQuestionCircle,
  faSignOutAlt,
  IconDefinition,
} from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store';

export interface UserDropdownProps {
  /** Callback to close the dropdown */
  onClose: () => void;
}

interface DropdownItemProps {
  icon: IconDefinition;
  label: string;
  onClick: () => void;
  isLogout?: boolean;
}

/**
 * Dropdown menu item component with consistent styling and hover states
 */
const DropdownItem: React.FC<DropdownItemProps> = ({
  icon,
  label,
  onClick,
  isLogout,
}) => (
  <Box
    as="button"
    w="100%"
    p={3}
    display="flex"
    alignItems="center"
    gap={3}
    cursor="pointer"
    borderRadius="md"
    bg="transparent"
    color={isLogout ? 'error.600' : 'text.primary'}
    _hover={{
      bg: isLogout ? 'error.50' : 'interactive.hover',
      color: isLogout ? 'error.700' : 'primary.800',
    }}
    _focus={{
      outline: '2px solid',
      outlineColor: isLogout ? 'error.500' : 'border.emphasis',
      outlineOffset: '2px',
    }}
    transition="all 0.2s ease-in-out"
    fontSize="sm"
    fontWeight="medium"
    textAlign="left"
    onClick={onClick}
    role="menuitem"
    tabIndex={0}
  >
    <Box as={FontAwesomeIcon} icon={icon} boxSize="16px" />
    <Text>{label}</Text>
  </Box>
);

/**
 * User dropdown menu component with navigation options and logout functionality.
 *
 * Features:
 * - Profile, Settings, Help & Support, Logout options
 * - Smooth animations and hover states
 * - Keyboard navigation support
 * - Proper ARIA labels for accessibility
 * - Responsive positioning
 */
const UserDropdown: React.FC<UserDropdownProps> = ({ onClose }) => {
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.actions.logout);
  const user = useAuthStore((state) => state.user);

  // Responsive positioning - adjust for mobile
  const dropdownWidth = useBreakpointValue({ base: '200px', md: '220px' });
  const rightOffset = useBreakpointValue({ base: '0', md: '0' });

  const handleProfile = () => {
    onClose();
    // Navigate to profile page when implemented
    console.log('Navigate to profile');
  };

  const handleSettings = () => {
    onClose();
    // Navigate to settings page when implemented
    console.log('Navigate to settings');
  };

  const handleHelp = () => {
    onClose();
    // Navigate to help page when implemented
    console.log('Navigate to help & support');
  };

  const handleLogout = () => {
    logout();
    onClose();
    navigate('/');
  };

  return (
    <Box
      position="absolute"
      top="100%"
      right={rightOffset}
      mt={2}
      w={dropdownWidth}
      bg="bg.surface"
      borderRadius="lg"
      boxShadow="lg"
      border="1px solid"
      borderColor="border.default"
      zIndex={1000}
      py={2}
      role="menu"
      aria-label="User menu options"
      // Animation
      opacity={1}
      transform="translateY(0)"
      transition="all 0.2s ease-in-out"
      // Prevent clicks from bubbling up
      onClick={(e) => e.stopPropagation()}
    >
      {/* User Info Header */}
      {user && (
        <>
          <Box px={3} py={2}>
            <Text fontSize="xs" color="text.muted" fontWeight="medium">
              Signed in as
            </Text>
            <Text
              fontSize="sm"
              color="primary.800"
              fontWeight="bold"
              isTruncated
            >
              {user.username}
            </Text>
          </Box>
          <Divider />
        </>
      )}

      {/* Menu Items */}
      <VStack spacing={0} py={2}>
        <DropdownItem icon={faUser} label="Profile" onClick={handleProfile} />
        <DropdownItem icon={faCog} label="Settings" onClick={handleSettings} />
        <DropdownItem
          icon={faQuestionCircle}
          label="Help & Support"
          onClick={handleHelp}
        />

        <Divider my={2} />

        <DropdownItem
          icon={faSignOutAlt}
          label="Logout"
          onClick={handleLogout}
          isLogout
        />
      </VStack>
    </Box>
  );
};

export default UserDropdown;
