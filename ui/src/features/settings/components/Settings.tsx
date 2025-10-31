import {
  Box,
  Container,
  Heading,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Input,
  Button,
  Text,
  Select,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Switch,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useToast,
  Divider,
  Card,
  CardBody,
  Flex,
  Icon,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
} from '@chakra-ui/react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faUser,
  faLock,
  faEdit,
  faEye,
  faDatabase,
  faExclamationTriangle,
} from '@fortawesome/free-solid-svg-icons';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSettingsStore } from '../store';
import { useAuthStore } from '../../auth/store';
import * as api from '../../../services/api';
import { handleError } from '../../../utils/errorHandler';

const Settings = () => {
  const toast = useToast();
  const navigate = useNavigate();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  // Store state
  const { editorPreferences, appearancePreferences, actions } =
    useSettingsStore();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.actions.logout);

  // Local state for forms
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [deletePassword, setDeletePassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [userInfo, setUserInfo] = useState<{
    username: string;
    created_at: string;
    notes_count: number;
  } | null>(null);

  // Load user info on mount
  useEffect(() => {
    const loadUserInfo = async () => {
      try {
        const info = await api.getUserInfo();
        setUserInfo(info);
      } catch (error: unknown) {
        const appError = handleError(error);
        toast({
          title: 'Error loading user info',
          description: appError.message,
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    };
    loadUserInfo();
  }, [toast]);

  // Format date for display
  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Password change handler
  const handlePasswordChange = async () => {
    if (newPassword !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        description: 'New password and confirm password must be the same',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    if (newPassword.length < 4) {
      toast({
        title: 'Password too short',
        description: 'Password must be at least 4 characters',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setIsChangingPassword(true);
    try {
      await api.changePassword(currentPassword, newPassword);
      toast({
        title: 'Password changed',
        description: 'Your password has been updated successfully',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      onClose();
    } catch (error: unknown) {
      const appError = handleError(error);
      toast({
        title: 'Failed to change password',
        description: appError.message,
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
      const blob = await api.exportNotes();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `parchmark_notes_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: 'Notes exported',
        description: 'Your notes have been downloaded successfully',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    } catch (error: unknown) {
      const appError = handleError(error);
      toast({
        title: 'Failed to export notes',
        description: appError.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsExporting(false);
    }
  };

  // Delete account handler
  const handleDeleteAccount = async () => {
    setIsDeletingAccount(true);
    try {
      await api.deleteAccount(deletePassword);
      toast({
        title: 'Account deleted',
        description: 'Your account has been permanently deleted',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      logout();
      navigate('/login');
    } catch (error: unknown) {
      const appError = handleError(error);
      toast({
        title: 'Failed to delete account',
        description: appError.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsDeletingAccount(false);
    }
  };

  return (
    <Box minH="100vh" bg="bg.canvas">
      <Container maxW="container.md" py={8}>
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <Box>
            <Heading size="lg" mb={2}>
              Settings
            </Heading>
            <Text color="text.secondary">
              Manage your account preferences and settings
            </Text>
          </Box>

          {/* Collapsible Sections */}
          <Accordion allowMultiple defaultIndex={[0]}>
            {/* Profile Information */}
            <AccordionItem>
              <h2>
                <AccordionButton>
                  <Box flex="1" textAlign="left">
                    <HStack spacing={3}>
                      <Icon as={FontAwesomeIcon} icon={faUser} />
                      <Text fontWeight="semibold" fontSize="lg">
                        Profile Information
                      </Text>
                    </HStack>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <Card>
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <FormControl>
                        <FormLabel>Username</FormLabel>
                        <Input value={user?.username || ''} isReadOnly />
                      </FormControl>

                      {userInfo && (
                        <>
                          <FormControl>
                            <FormLabel>Member Since</FormLabel>
                            <Input
                              value={formatDate(userInfo.created_at)}
                              isReadOnly
                            />
                          </FormControl>

                          <Box
                            p={4}
                            borderRadius="md"
                            bg="primary.50"
                            _dark={{ bg: 'primary.900' }}
                          >
                            <Text fontWeight="semibold" mb={2}>
                              Account Statistics
                            </Text>
                            <Text>
                              Total Notes:{' '}
                              <strong>{userInfo.notes_count}</strong>
                            </Text>
                          </Box>
                        </>
                      )}
                    </VStack>
                  </CardBody>
                </Card>
              </AccordionPanel>
            </AccordionItem>

            {/* Password & Security */}
            <AccordionItem>
              <h2>
                <AccordionButton>
                  <Box flex="1" textAlign="left">
                    <HStack spacing={3}>
                      <Icon as={FontAwesomeIcon} icon={faLock} />
                      <Text fontWeight="semibold" fontSize="lg">
                        Password & Security
                      </Text>
                    </HStack>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <Card>
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <Text color="text.secondary">
                        Keep your account secure by using a strong password
                      </Text>
                      <Button
                        leftIcon={<FontAwesomeIcon icon={faLock} />}
                        colorScheme="primary"
                        onClick={onOpen}
                      >
                        Change Password
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              </AccordionPanel>
            </AccordionItem>

            {/* Editor Preferences */}
            <AccordionItem>
              <h2>
                <AccordionButton>
                  <Box flex="1" textAlign="left">
                    <HStack spacing={3}>
                      <Icon as={FontAwesomeIcon} icon={faEdit} />
                      <Text fontWeight="semibold" fontSize="lg">
                        Editor Preferences
                      </Text>
                    </HStack>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <Card>
                  <CardBody>
                    <VStack spacing={6} align="stretch">
                      <FormControl>
                        <FormLabel>Font Family</FormLabel>
                        <Select
                          value={editorPreferences.fontFamily}
                          onChange={(e) =>
                            actions.updateEditorPreferences({
                              fontFamily: e.target.value as
                                | 'monospace'
                                | 'sans-serif'
                                | 'serif',
                            })
                          }
                        >
                          <option value="monospace">Monospace</option>
                          <option value="sans-serif">Sans Serif</option>
                          <option value="serif">Serif</option>
                        </Select>
                      </FormControl>

                      <FormControl>
                        <FormLabel>
                          Font Size: {editorPreferences.fontSize}px
                        </FormLabel>
                        <Slider
                          min={12}
                          max={24}
                          step={1}
                          value={editorPreferences.fontSize}
                          onChange={(val) =>
                            actions.updateEditorPreferences({ fontSize: val })
                          }
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                      </FormControl>

                      <FormControl>
                        <FormLabel>
                          Line Height: {editorPreferences.lineHeight.toFixed(1)}
                        </FormLabel>
                        <Slider
                          min={1.2}
                          max={2.0}
                          step={0.1}
                          value={editorPreferences.lineHeight}
                          onChange={(val) =>
                            actions.updateEditorPreferences({ lineHeight: val })
                          }
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                      </FormControl>

                      <FormControl>
                        <FormLabel>Auto-save Delay</FormLabel>
                        <Select
                          value={editorPreferences.autoSaveDelay}
                          onChange={(e) =>
                            actions.updateEditorPreferences({
                              autoSaveDelay: Number(e.target.value),
                            })
                          }
                        >
                          <option value={0}>Immediate</option>
                          <option value={1000}>1 second</option>
                          <option value={3000}>3 seconds</option>
                          <option value={5000}>5 seconds</option>
                        </Select>
                      </FormControl>

                      <HStack justify="space-between">
                        <FormLabel mb={0}>Word Wrap</FormLabel>
                        <Switch
                          isChecked={editorPreferences.wordWrap}
                          onChange={(e) =>
                            actions.updateEditorPreferences({
                              wordWrap: e.target.checked,
                            })
                          }
                        />
                      </HStack>

                      <HStack justify="space-between">
                        <FormLabel mb={0}>Spell Check</FormLabel>
                        <Switch
                          isChecked={editorPreferences.spellCheck}
                          onChange={(e) =>
                            actions.updateEditorPreferences({
                              spellCheck: e.target.checked,
                            })
                          }
                        />
                      </HStack>
                    </VStack>
                  </CardBody>
                </Card>
              </AccordionPanel>
            </AccordionItem>

            {/* Appearance */}
            <AccordionItem>
              <h2>
                <AccordionButton>
                  <Box flex="1" textAlign="left">
                    <HStack spacing={3}>
                      <Icon as={FontAwesomeIcon} icon={faEye} />
                      <Text fontWeight="semibold" fontSize="lg">
                        Appearance
                      </Text>
                    </HStack>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <Card>
                  <CardBody>
                    <VStack spacing={6} align="stretch">
                      <FormControl>
                        <FormLabel>
                          Sidebar Width: {appearancePreferences.sidebarWidth}px
                        </FormLabel>
                        <Slider
                          min={200}
                          max={400}
                          step={20}
                          value={appearancePreferences.sidebarWidth}
                          onChange={(val) =>
                            actions.updateAppearancePreferences({
                              sidebarWidth: val,
                            })
                          }
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb />
                        </Slider>
                      </FormControl>

                      <Text fontSize="sm" color="text.secondary">
                        Color theme can be changed using the theme toggle in the
                        header
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>
              </AccordionPanel>
            </AccordionItem>

            {/* Data Management */}
            <AccordionItem>
              <h2>
                <AccordionButton>
                  <Box flex="1" textAlign="left">
                    <HStack spacing={3}>
                      <Icon as={FontAwesomeIcon} icon={faDatabase} />
                      <Text fontWeight="semibold" fontSize="lg">
                        Data Management
                      </Text>
                    </HStack>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <Card>
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <Box>
                        <Text fontWeight="semibold" mb={2}>
                          Export Your Data
                        </Text>
                        <Text fontSize="sm" color="text.secondary" mb={3}>
                          Download all your notes as a ZIP file containing
                          individual markdown files and metadata
                        </Text>
                        <Button
                          colorScheme="blue"
                          onClick={handleExportNotes}
                          isLoading={isExporting}
                        >
                          Export All Notes
                        </Button>
                      </Box>

                      <Divider />

                      {userInfo && (
                        <Box
                          p={4}
                          borderRadius="md"
                          bg="primary.50"
                          _dark={{ bg: 'primary.900' }}
                        >
                          <Text fontWeight="semibold" mb={2}>
                            Storage Statistics
                          </Text>
                          <Text fontSize="sm">
                            You have {userInfo.notes_count} note
                            {userInfo.notes_count !== 1 ? 's' : ''} stored
                          </Text>
                        </Box>
                      )}
                    </VStack>
                  </CardBody>
                </Card>
              </AccordionPanel>
            </AccordionItem>

            {/* Danger Zone */}
            <AccordionItem>
              <h2>
                <AccordionButton>
                  <Box flex="1" textAlign="left">
                    <HStack spacing={3}>
                      <Icon
                        as={FontAwesomeIcon}
                        icon={faExclamationTriangle}
                        color="red.500"
                      />
                      <Text fontWeight="semibold" fontSize="lg" color="red.500">
                        Danger Zone
                      </Text>
                    </HStack>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
              </h2>
              <AccordionPanel pb={4}>
                <Alert status="error" borderRadius="md" mb={4}>
                  <AlertIcon />
                  <Box>
                    <AlertTitle>Warning!</AlertTitle>
                    <AlertDescription>
                      These actions are permanent and cannot be undone
                    </AlertDescription>
                  </Box>
                </Alert>

                <Card borderColor="red.500" borderWidth={1}>
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <Box>
                        <Text fontWeight="semibold" mb={2}>
                          Delete Account
                        </Text>
                        <Text fontSize="sm" color="text.secondary" mb={3}>
                          Permanently delete your account and all associated
                          notes. This action cannot be undone.
                        </Text>
                        <Button
                          colorScheme="red"
                          onClick={onDeleteOpen}
                          leftIcon={
                            <FontAwesomeIcon icon={faExclamationTriangle} />
                          }
                        >
                          Delete Account
                        </Button>
                      </Box>
                    </VStack>
                  </CardBody>
                </Card>
              </AccordionPanel>
            </AccordionItem>
          </Accordion>

          {/* Reset to Defaults Button */}
          <Flex justify="center" mt={4}>
            <Button
              variant="outline"
              onClick={() => {
                actions.resetToDefaults();
                toast({
                  title: 'Settings reset',
                  description: 'All preferences have been reset to defaults',
                  status: 'info',
                  duration: 3000,
                  isClosable: true,
                });
              }}
            >
              Reset All Preferences to Defaults
            </Button>
          </Flex>
        </VStack>
      </Container>

      {/* Change Password Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
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
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>New Password</FormLabel>
                <Input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Confirm New Password</FormLabel>
                <Input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="primary"
              onClick={handlePasswordChange}
              isLoading={isChangingPassword}
            >
              Change Password
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Delete Account Modal */}
      <Modal isOpen={isDeleteOpen} onClose={onDeleteClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Delete Account</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Alert status="error">
                <AlertIcon />
                <Box>
                  <AlertTitle>This action cannot be undone!</AlertTitle>
                  <AlertDescription>
                    All your notes and data will be permanently deleted
                  </AlertDescription>
                </Box>
              </Alert>

              <FormControl isRequired>
                <FormLabel>Confirm your password to continue</FormLabel>
                <Input
                  type="password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  placeholder="Enter your password"
                />
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onDeleteClose}>
              Cancel
            </Button>
            <Button
              colorScheme="red"
              onClick={handleDeleteAccount}
              isLoading={isDeletingAccount}
            >
              Delete My Account
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Settings;
