import React from 'react';
import { Button } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSignInAlt } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';
import { COLORS } from '../../../../utils/constants';

/**
 * Login button component displayed when user is not authenticated.
 * Navigates to /login route when clicked.
 */
const LoginButton: React.FC = () => {
  const navigate = useNavigate();

  const handleSignIn = () => {
    navigate('/login');
  };

  return (
    <Button
      onClick={handleSignIn}
      size="sm"
      variant="outline"
      borderColor={COLORS.primaryColor}
      color={COLORS.primaryColor}
      bg="white"
      _hover={{
        bg: COLORS.primaryColor,
        color: 'white',
        transform: 'translateY(-1px)',
        boxShadow: 'sm',
      }}
      _active={{
        transform: 'translateY(0)',
      }}
      transition="all 0.2s ease-in-out"
      leftIcon={<FontAwesomeIcon icon={faSignInAlt} />}
      fontWeight="medium"
      px={4}
      aria-label="Sign in to your account"
    >
      Sign In
    </Button>
  );
};

export default LoginButton;