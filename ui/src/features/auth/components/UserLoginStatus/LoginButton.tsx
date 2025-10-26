import React from 'react';
import { Button } from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSignInAlt } from '@fortawesome/free-solid-svg-icons';
import { useNavigate } from 'react-router-dom';

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
      variant="secondary"
      leftIcon={<FontAwesomeIcon icon={faSignInAlt} />}
      fontWeight="medium"
      px={4}
      aria-label="Sign in to your account"
      _hover={{ transform: 'translateY(-1px)' }}
      _active={{ transform: 'translateY(0)' }}
    >
      Sign In
    </Button>
  );
};

export default LoginButton;
