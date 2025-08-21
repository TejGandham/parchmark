import React from 'react';
import { Box } from '@chakra-ui/react';
import { useAuthStore } from '../../store';
import LoginButton from './LoginButton';
import UserInfo from './UserInfo';

export interface UserLoginStatusProps {
  /** Optional className for styling */
  className?: string;
}

/**
 * User login status component that displays either a login button (when logged out)
 * or user info with dropdown menu (when logged in).
 * 
 * Features:
 * - Responsive design: full display on desktop, avatar-only on mobile
 * - Integrates with existing Zustand auth store
 * - Smooth animations and hover states
 * - Accessibility compliant with ARIA labels and keyboard navigation
 */
const UserLoginStatus: React.FC<UserLoginStatusProps> = ({ className }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return (
    <Box className={className} role="region" aria-label="User authentication status">
      {isAuthenticated ? <UserInfo /> : <LoginButton />}
    </Box>
  );
};

export default UserLoginStatus;