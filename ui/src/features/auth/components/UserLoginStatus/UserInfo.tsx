import React, { useState, useRef, useEffect } from 'react';
import {
  HStack,
  Avatar,
  Text,
  Box,
  useBreakpointValue,
  Flex,
} from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChevronDown } from '@fortawesome/free-solid-svg-icons';
import { useAuthStore } from '../../store';
import UserDropdown from './UserDropdown';

/**
 * User info component displayed when user is authenticated.
 * Shows user avatar, username (on desktop), and dropdown menu on click.
 *
 * Features:
 * - Responsive: shows username on desktop, avatar only on mobile
 * - Click to open/close dropdown menu
 * - Click outside to close dropdown
 * - Keyboard navigation support
 */
const UserInfo: React.FC = () => {
  const user = useAuthStore((state) => state.user);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Responsive breakpoint - show username on md and up, hide on smaller screens
  const showUsername = useBreakpointValue({ base: false, md: true });

  // Get user initials for avatar
  const getUserInitials = (username: string): string => {
    return username
      .split(' ')
      .map((name) => name.charAt(0).toUpperCase())
      .join('')
      .substring(0, 2);
  };

  // Truncate username if longer than 12 characters
  const getDisplayUsername = (username: string): string => {
    return username.length > 12 ? `${username.substring(0, 12)}...` : username;
  };

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const closeDropdown = () => {
    setIsDropdownOpen(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        closeDropdown();
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggleDropdown();
    } else if (event.key === 'Escape') {
      closeDropdown();
    }
  };

  if (!user) return null;

  return (
    <Box ref={containerRef} position="relative">
      <Flex
        align="center"
        cursor="pointer"
        onClick={toggleDropdown}
        onKeyDown={handleKeyDown}
        tabIndex={0}
        role="button"
        aria-expanded={isDropdownOpen}
        aria-haspopup="menu"
        aria-label={`User menu for ${user.username}`}
        p={1}
        borderRadius="md"
        _hover={{
          bg: 'interactive.hover',
        }}
        _focus={{
          outline: '2px solid',
          outlineColor: 'border.emphasis',
          outlineOffset: '2px',
        }}
        transition="all 0.2s ease-in-out"
      >
        <HStack spacing={2}>
          {/* User Avatar */}
          <Avatar
            size="sm"
            name={user.username}
            getInitials={getUserInitials}
            bgGradient="linear(to-br, primary.800, primary.600)"
            color="white"
            fontWeight="bold"
            fontSize="sm"
          />

          {/* Username - hidden on mobile */}
          {showUsername && (
            <Text
              fontSize="sm"
              fontWeight="medium"
              color="primary.800"
              maxW="120px"
              isTruncated
            >
              {getDisplayUsername(user.username)}
            </Text>
          )}

          {/* Dropdown Arrow */}
          <Box
            as={FontAwesomeIcon}
            icon={faChevronDown}
            fontSize="xs"
            color="primary.800"
            transform={isDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)'}
            transition="transform 0.2s ease-in-out"
            ml={1}
          />
        </HStack>
      </Flex>

      {/* Dropdown Menu */}
      {isDropdownOpen && <UserDropdown onClose={closeDropdown} />}
    </Box>
  );
};

export default UserInfo;
