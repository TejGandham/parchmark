import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Heading,
  HStack,
  IconButton,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stat,
  StatLabel,
  StatNumber,
  Text,
  useDisclosure,
  useToast,
  VStack,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Alert,
  AlertIcon,
  Spinner,
  Center,
} from '@chakra-ui/react';
import { ArrowBackIcon } from '@chakra-ui/icons';
import {
  getUserInfo,
  changePassword,
  exportNotes,
  deleteAccount,
  UserInfo,
} from '../../../services/api';
import { useAuthStore } from '../../auth/store';

const Settings = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const logout = useAuthStore((state) => state.actions.logout);

  // User info state
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [isLoadingUserInfo, setIsLoadingUserInfo] = useState(true);

  // Password change state
  const {
    isOpen: isPasswordModalOpen,
    onOpen: onPasswordModalOpen,
    onClose: onPasswordModalClose,
  } = useDisclosure();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Delete account state
  const {
    isOpen: isDeleteModalOpen,
    onOpen: onDeleteModalOpen,
    onClose: onDeleteModalClose,
  } = useDisclosure();
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);

  // Export state
  const [isExporting, setIsExporting] = useState(false);

  // Load user info on mount
  useEffect(() => {
    const loadUserInfo = async () => {
      try {
        const info = await getUserInfo();
        setUserInfo(info);
      } catch (error) {
        toast({
          title: 'Error loading user info',
          description: error instanceof Error ? error.message : 'Unknown error',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      } finally {
        setIsLoadingUserInfo(false);
      }
    };
    loadUserInfo();
  }, [toast]);

  // Password change handler
  const handlePasswordChange = async () => {
    if (newPassword !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (newPassword.length < 4) {
      toast({
        title: 'Password too short',
        description: 'Password must be at least 4 characters',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsChangingPassword(true);
    try {
      await changePassword(currentPassword, newPassword);
      toast({
        title: 'Password changed successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      onPasswordModalClose();
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      toast({
        title: 'Failed to change password',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsChangingPassword(false);
    }
  };

  // Export notes handler
  const handleExportNotes = async () => {
    setIsExporting(true);
    try {
      const blob = await exportNotes();
      if (blob.size === 0) {
        toast({
          title: 'Failed to export notes',
          description: 'Export returned empty data',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
        return;
      }

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `parchmark_notes_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Notes exported',
        description: 'Your notes have been downloaded as a ZIP file',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Failed to export notes',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsExporting(false);
    }
  };

  // Delete account handler
  // Note: Form validations are enforced via button disabled state
  const handleDeleteAccount = async () => {
    setIsDeletingAccount(true);
    try {
      await deleteAccount(deletePassword || 'DELETE');
      toast({
        title: 'Account deleted',
        description: 'Your account has been permanently deleted',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      logout();
      navigate('/login');
    } catch (error) {
      toast({
        title: 'Failed to delete account',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsDeletingAccount(false);
    }
  };

  // Reset modals on close
  const handlePasswordModalClose = () => {
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    onPasswordModalClose();
  };

  const handleDeleteModalClose = () => {
    setDeletePassword('');
    setDeleteConfirmText('');
    onDeleteModalClose();
  };

  if (isLoadingUserInfo) {
    return (
      <Center h="100vh">
        <Spinner size="xl" />
      </Center>
    );
  }

  const isOIDCUser = userInfo?.auth_provider === 'oidc';

  return (
    <Box minH="100vh" bg="gray.50" py={8}>
      <Container maxW="container.md">
        {/* Header */}
        <HStack mb={8}>
          <IconButton
            aria-label="Back to notes"
            icon={<ArrowBackIcon />}
            onClick={() => navigate('/notes')}
            variant="ghost"
          />
          <Heading size="lg">Settings</Heading>
        </HStack>

        {/* Accordion Sections */}
        <Accordion allowMultiple defaultIndex={[0]}>
          {/* Profile Information */}
          <AccordionItem
            bg="white"
            borderRadius="md"
            border="1px solid"
            borderColor="gray.200"
            mb={4}
          >
            <h2>
              <AccordionButton py={4}>
                <Box flex="1" textAlign="left" fontWeight="semibold">
                  Profile Information
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4}>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>Username</FormLabel>
                  <Input value={userInfo?.username || ''} isReadOnly />
                </FormControl>

                {userInfo?.email && (
                  <FormControl>
                    <FormLabel>Email</FormLabel>
                    <Input value={userInfo.email} isReadOnly />
                  </FormControl>
                )}

                <HStack spacing={8}>
                  <Stat>
                    <StatLabel>Member Since</StatLabel>
                    <StatNumber fontSize="md">
                      {userInfo?.created_at
                        ? new Date(userInfo.created_at).toLocaleDateString()
                        : 'Unknown'}
                    </StatNumber>
                  </Stat>
                  <Stat>
                    <StatLabel>Total Notes</StatLabel>
                    <StatNumber fontSize="md">
                      {userInfo?.notes_count ?? 0}
                    </StatNumber>
                  </Stat>
                </HStack>

                {isOIDCUser && (
                  <Alert status="info" borderRadius="md">
                    <AlertIcon />
                    <Text fontSize="sm">
                      You are signed in via Single Sign-On (SSO). Some settings
                      may be managed by your identity provider.
                    </Text>
                  </Alert>
                )}
              </VStack>
            </AccordionPanel>
          </AccordionItem>

          {/* Password & Security - Only for local users */}
          {!isOIDCUser && (
            <AccordionItem
              bg="white"
              borderRadius="md"
              border="1px solid"
              borderColor="gray.200"
              mb={4}
            >
              <h2>
                <AccordionButton py={4}>
                  <Box flex="1" textAlign="left" fontWeight="semibold">
                    Password & Security
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <Text mb={4} color="gray.600">
                  Keep your account secure by using a strong password.
                </Text>
                <Button colorScheme="primary" onClick={onPasswordModalOpen}>
                  Change Password
                </Button>
              </AccordionPanel>
            </AccordionItem>
          )}

          {/* Data Management */}
          <AccordionItem
            bg="white"
            borderRadius="md"
            border="1px solid"
            borderColor="gray.200"
            mb={4}
          >
            <h2>
              <AccordionButton py={4}>
                <Box flex="1" textAlign="left" fontWeight="semibold">
                  Data Management
                </Box>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4}>
              <VStack spacing={4} align="stretch">
                <Text color="gray.600">
                  Export all your notes as a ZIP file containing markdown files
                  and metadata.
                </Text>
                <Button
                  colorScheme="primary"
                  onClick={handleExportNotes}
                  isLoading={isExporting}
                  loadingText="Exporting..."
                >
                  Export All Notes
                </Button>
              </VStack>
            </AccordionPanel>
          </AccordionItem>

          {/* Danger Zone */}
          <AccordionItem
            bg="red.50"
            borderRadius="md"
            border="1px solid"
            borderColor="red.300"
            mb={4}
          >
            <h2>
              <AccordionButton py={4}>
                <Box
                  flex="1"
                  textAlign="left"
                  fontWeight="semibold"
                  color="red.600"
                >
                  Danger Zone
                </Box>
                <AccordionIcon color="red.600" />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4}>
              <VStack spacing={4} align="stretch">
                <Alert status="warning" borderRadius="md">
                  <AlertIcon />
                  <Text fontSize="sm">
                    Deleting your account is permanent and cannot be undone. All
                    your notes will be permanently deleted.
                  </Text>
                </Alert>
                <Button colorScheme="red" onClick={onDeleteModalOpen}>
                  Delete Account
                </Button>
              </VStack>
            </AccordionPanel>
          </AccordionItem>
        </Accordion>
      </Container>

      {/* Password Change Modal */}
      <Modal isOpen={isPasswordModalOpen} onClose={handlePasswordModalClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Change Password</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Current Password</FormLabel>
                <Input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>New Password</FormLabel>
                <Input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Confirm New Password</FormLabel>
                <Input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={handlePasswordModalClose}>
              Cancel
            </Button>
            <Button
              colorScheme="primary"
              onClick={handlePasswordChange}
              isLoading={isChangingPassword}
              isDisabled={!currentPassword || !newPassword || !confirmPassword}
            >
              Change Password
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Account Modal */}
      <Modal isOpen={isDeleteModalOpen} onClose={handleDeleteModalClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader color="red.600">Delete Account</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <Alert status="error" borderRadius="md">
                <AlertIcon />
                <Text fontSize="sm">
                  This action is irreversible. All your data will be permanently
                  deleted.
                </Text>
              </Alert>

              {!isOIDCUser && (
                <FormControl isRequired>
                  <FormLabel>Enter your password</FormLabel>
                  <Input
                    type="password"
                    value={deletePassword}
                    onChange={(e) => setDeletePassword(e.target.value)}
                    placeholder="Enter your password"
                  />
                </FormControl>
              )}

              <FormControl isRequired>
                <FormLabel>Type DELETE to confirm</FormLabel>
                <Input
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  placeholder="DELETE"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={handleDeleteModalClose}>
              Cancel
            </Button>
            <Button
              colorScheme="red"
              onClick={handleDeleteAccount}
              isLoading={isDeletingAccount}
              isDisabled={
                deleteConfirmText !== 'DELETE' ||
                (!isOIDCUser && deletePassword.length < 4)
              }
            >
              Delete Account
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Settings;
