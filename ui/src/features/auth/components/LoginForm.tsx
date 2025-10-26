import { useState, FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  InputGroup,
  InputLeftElement,
  InputRightElement,
  IconButton,
  VStack,
  Heading,
  Text,
  Alert,
  AlertIcon,
  FormErrorMessage,
  Grid,
  Flex,
  Image,
  useBreakpointValue,
} from '@chakra-ui/react';
import { ViewIcon, ViewOffIcon, LockIcon } from '@chakra-ui/icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser } from '@fortawesome/free-solid-svg-icons';
import { useAuthStore } from '../store';
import Logo from '../../../../assets/images/parchmark.svg';

const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  // Access the auth store directly to avoid infinite loops
  const authStore = useAuthStore();
  const error = authStore.error;
  const actions = authStore.actions;
  const navigate = useNavigate();
  const location = useLocation();

  // Responsive: show brand panel only on larger screens
  const showBrandPanel = useBreakpointValue({ base: false, md: true });
  const gridTemplate = useBreakpointValue({
    base: '1fr',
    md: '1.5fr 1fr',
  });

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
    <Grid
      minH="100vh"
      templateColumns={gridTemplate}
      bgGradient="linear(135deg, neutral.50 0%, neutral.100 100%)"
    >
      {/* Left Brand Panel - Only show on md+ screens */}
      {showBrandPanel && (
        <Flex
          bgGradient="linear(to-br, primary.800, primary.600)"
          direction="column"
          justify="center"
          align="center"
          p={12}
          position="relative"
          overflow="hidden"
        >
          {/* Subtle decorative background */}
          <Box
            position="absolute"
            top="0"
            left="0"
            right="0"
            bottom="0"
            opacity="0.1"
            bgImage="radial-gradient(circle, white 1px, transparent 1px)"
            bgSize="30px 30px"
          />

          {/* Content */}
          <VStack spacing={8} position="relative" zIndex={1} color="white">
            <Image
              src={Logo}
              alt="ParchMark"
              h="80px"
              filter="brightness(0) invert(1)"
            />

            <Heading
              as="h1"
              size="2xl"
              fontFamily="'Playfair Display', serif"
              textAlign="center"
              letterSpacing="tight"
            >
              Welcome to ParchMark
            </Heading>

            <Text fontSize="xl" textAlign="center" maxW="md" opacity={0.9}>
              Your thoughts, beautifully preserved
            </Text>

            <VStack spacing={3} mt={8} align="flex-start">
              <Text fontSize="md" opacity={0.8}>
                ✦ Elegant markdown note-taking
              </Text>
              <Text fontSize="md" opacity={0.8}>
                ✦ Beautiful, distraction-free interface
              </Text>
              <Text fontSize="md" opacity={0.8}>
                ✦ Your notes, your way
              </Text>
            </VStack>
          </VStack>
        </Flex>
      )}

      {/* Right Form Panel */}
      <Flex justify="center" align="center" p={{ base: 6, md: 12 }}>
        <Box
          bg="bg.surface"
          p={{ base: 8, md: 12 }}
          borderRadius="xl"
          boxShadow="0 20px 60px rgba(88, 12, 36, 0.15), 0 0 1px rgba(88, 12, 36, 0.1)"
          maxW="md"
          w="full"
        >
          <VStack spacing={6} align="stretch">
            {/* Heading */}
            <VStack spacing={2} align="stretch">
              <Heading
                as="h2"
                size="xl"
                fontFamily="'Playfair Display', serif"
                color="primary.800"
                letterSpacing="tight"
              >
                Sign In
              </Heading>
              <Text color="text.muted" fontSize="md">
                Welcome back! Please enter your credentials
              </Text>
            </VStack>

            {/* Error Alert */}
            {error && (
              <Alert status="error" borderRadius="md" variant="left-accent">
                <AlertIcon />
                {error}
              </Alert>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit}>
              <VStack spacing={5}>
                {/* Username Input with Icon */}
                <FormControl isInvalid={!!usernameError} isRequired>
                  <FormLabel color="text.primary" fontWeight="medium">
                    Username
                  </FormLabel>
                  <InputGroup>
                    <InputLeftElement pointerEvents="none" color="text.muted">
                      <FontAwesomeIcon icon={faUser} />
                    </InputLeftElement>
                    <Input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Enter your username"
                      data-testid="username-input"
                      pl="2.75rem"
                      borderWidth="2px"
                      _focus={{
                        borderColor: 'primary.800',
                        boxShadow: '0 0 0 3px rgba(88, 12, 36, 0.1)',
                      }}
                    />
                  </InputGroup>
                  <FormErrorMessage>{usernameError}</FormErrorMessage>
                </FormControl>

                {/* Password Input with Icons */}
                <FormControl isInvalid={!!passwordError} isRequired>
                  <FormLabel color="text.primary" fontWeight="medium">
                    Password
                  </FormLabel>
                  <InputGroup>
                    <InputLeftElement pointerEvents="none" color="text.muted">
                      <LockIcon />
                    </InputLeftElement>
                    <Input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      data-testid="password-input"
                      pl="2.75rem"
                      borderWidth="2px"
                      _focus={{
                        borderColor: 'primary.800',
                        boxShadow: '0 0 0 3px rgba(88, 12, 36, 0.1)',
                      }}
                    />
                    <InputRightElement>
                      <IconButton
                        aria-label={
                          showPassword ? 'Hide password' : 'Show password'
                        }
                        icon={showPassword ? <ViewOffIcon /> : <ViewIcon />}
                        onClick={() => setShowPassword(!showPassword)}
                        variant="ghost"
                        size="sm"
                        data-testid="password-toggle"
                      />
                    </InputRightElement>
                  </InputGroup>
                  <FormErrorMessage>{passwordError}</FormErrorMessage>
                </FormControl>

                {/* Submit Button */}
                <Button
                  type="submit"
                  colorScheme="primary"
                  size="lg"
                  width="full"
                  mt={2}
                  isLoading={isLoading}
                  data-testid="login-button"
                  fontWeight="semibold"
                  boxShadow="0 4px 12px rgba(88, 12, 36, 0.25)"
                  _hover={{
                    transform: 'translateY(-2px)',
                    boxShadow: '0 6px 20px rgba(88, 12, 36, 0.35)',
                  }}
                  _active={{
                    transform: 'translateY(0)',
                  }}
                >
                  Sign In
                </Button>
              </VStack>
            </form>
          </VStack>
        </Box>
      </Flex>
    </Grid>
  );
};

export default LoginForm;
