import { useState, FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  InputGroup,
  InputRightElement,
  IconButton,
  VStack,
  Heading,
  Alert,
  AlertIcon,
  FormErrorMessage,
} from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';
import { useAuthStore } from '../store';

const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  // Access the auth store directly to avoid infinite loops
  const authStore = useAuthStore();
  const error = authStore.error;
  const actions = authStore.actions;
  const navigate = useNavigate();
  const location = useLocation();

  const validateForm = (): boolean => {
    let isValid = true;

    if (!username.trim()) {
      setUsernameError('Username is required');
      isValid = false;
    } else {
      setUsernameError('');
    }

    if (!password) {
      setPasswordError('Password is required');
      isValid = false;
    } else {
      setPasswordError('');
    }

    return isValid;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    const success = await actions.login(username, password);
    setIsLoading(false);

    if (success) {
      const from =
        (location.state as { from?: { pathname: string } })?.from?.pathname ||
        '/notes';
      navigate(from, { replace: true });
    }
  };

  return (
    <Box maxW="md" mx="auto" mt="20">
      <VStack spacing={8} align="stretch">
        <Heading textAlign="center">Login to Parchmark</Heading>

        {error && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <VStack spacing={4}>
            <FormControl isInvalid={!!usernameError} isRequired>
              <FormLabel>Username</FormLabel>
              <Input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                data-testid="username-input"
              />
              <FormErrorMessage>{usernameError}</FormErrorMessage>
            </FormControl>

            <FormControl isInvalid={!!passwordError} isRequired>
              <FormLabel>Password</FormLabel>
              <InputGroup>
                <Input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  data-testid="password-input"
                />
                <InputRightElement>
                  <IconButton
                    aria-label={
                      showPassword ? 'Hide password' : 'Show password'
                    }
                    icon={
                      <FontAwesomeIcon
                        icon={showPassword ? faEyeSlash : faEye}
                      />
                    }
                    onClick={() => setShowPassword(!showPassword)}
                    variant="ghost"
                    size="sm"
                    data-testid="toggle-password-visibility"
                  />
                </InputRightElement>
              </InputGroup>
              <FormErrorMessage>{passwordError}</FormErrorMessage>
            </FormControl>

            <Button
              type="submit"
              colorScheme="purple"
              width="full"
              mt={4}
              isLoading={isLoading}
              data-testid="login-button"
            >
              Login
            </Button>
          </VStack>
        </form>
      </VStack>
    </Box>
  );
};

export default LoginForm;
