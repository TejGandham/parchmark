import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Alert,
  AlertIcon,
  FormErrorMessage,
} from '@chakra-ui/react';
import { useAuthStore } from '../store';

const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  // Access the auth store directly to avoid infinite loops
  const authStore = useAuthStore();
  const error = authStore.error;
  const actions = authStore.actions;
  const navigate = useNavigate();

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

  // We removed the conditional console.log that was causing an infinite loop

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const success = actions.login(username, password);

    if (success) {
      navigate('/notes');
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
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                data-testid="password-input"
              />
              <FormErrorMessage>{passwordError}</FormErrorMessage>
            </FormControl>

            <Button
              type="submit"
              colorScheme="purple"
              width="full"
              mt={4}
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
