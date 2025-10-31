import { vi, Mock } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { useNavigate } from 'react-router-dom';
import { render } from '../../../../../test-utils/render';
import Settings from '../../../../features/settings/components/Settings';
import { useSettingsStore } from '../../../../features/settings/store';
import { useAuthStore } from '../../../../features/auth/store';
import * as api from '../../../../services/api';

// Mock the stores
vi.mock('../../../../features/settings/store');
vi.mock('../../../../features/auth/store');
vi.mock('../../../../services/api');

// Mock react-router's useNavigate
vi.mock('react-router-dom', async () => ({
  ...(await import('react-router-dom')),
  useNavigate: vi.fn(),
}));

// Mock toast
const mockToast = vi.fn();
vi.mock('@chakra-ui/react', async () => {
  const actual = await import('@chakra-ui/react');
  return {
    ...actual,
    useToast: () => mockToast,
  };
});

describe('Settings Component', () => {
  const mockNavigate = vi.fn();
  const mockLogout = vi.fn();
  const mockUpdateEditorPreferences = vi.fn();
  const mockUpdateAppearancePreferences = vi.fn();
  const mockResetToDefaults = vi.fn();

  const defaultSettingsStore = {
    editorPreferences: {
      fontFamily: 'monospace' as const,
      fontSize: 16,
      lineHeight: 1.6,
      autoSaveDelay: 1000,
      showLineNumbers: false,
      wordWrap: true,
      spellCheck: true,
    },
    appearancePreferences: {
      sidebarWidth: 280,
    },
    isLoading: false,
    error: null,
    actions: {
      updateEditorPreferences: mockUpdateEditorPreferences,
      updateAppearancePreferences: mockUpdateAppearancePreferences,
      resetToDefaults: mockResetToDefaults,
      clearError: vi.fn(),
    },
  };

  const defaultAuthStore = {
    user: { username: 'testuser', password: '' },
    actions: {
      logout: mockLogout,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useNavigate as Mock).mockReturnValue(mockNavigate);
    (useSettingsStore as Mock).mockReturnValue(defaultSettingsStore);
    (useAuthStore as Mock).mockImplementation((selector) => {
      if (typeof selector === 'function') {
        return selector(defaultAuthStore);
      }
      return defaultAuthStore;
    });
    mockToast.mockClear();

    // Mock API calls
    (api.getUserInfo as Mock).mockResolvedValue({
      username: 'testuser',
      created_at: '2025-01-01T00:00:00Z',
      notes_count: 5,
    });
  });

  describe('Rendering', () => {
    it('renders settings page with all sections', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(
          screen.getByRole('heading', { name: 'Settings' })
        ).toBeInTheDocument();
      });

      // Check for accordion sections
      expect(screen.getByText('Profile Information')).toBeInTheDocument();
      expect(screen.getByText('Password & Security')).toBeInTheDocument();
      expect(screen.getByText('Editor Preferences')).toBeInTheDocument();
      expect(screen.getByText('Appearance')).toBeInTheDocument();
      expect(screen.getByText('Data Management')).toBeInTheDocument();
      expect(screen.getByText('Danger Zone')).toBeInTheDocument();
    });

    it('loads and displays user info', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
      });

      expect(screen.getByText('Total Notes:')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('shows error toast if user info fails to load', async () => {
      (api.getUserInfo as Mock).mockRejectedValue(
        new Error('Failed to load user info')
      );

      render(<Settings />);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Error loading user info',
            status: 'error',
          })
        );
      });
    });
  });

  describe('Editor Preferences', () => {
    it('updates font family', async () => {
      render(<Settings />);

      const fontFamilySelect = screen.getByLabelText('Font Family');
      fireEvent.change(fontFamilySelect, { target: { value: 'sans-serif' } });

      expect(mockUpdateEditorPreferences).toHaveBeenCalledWith({
        fontFamily: 'sans-serif',
      });
    });

    it('updates font size with slider', async () => {
      render(<Settings />);

      // Font size slider
      const fontSizeSlider = screen
        .getByText('Font Size: 16px')
        .closest('div')
        ?.querySelector('[role="slider"]');

      if (fontSizeSlider) {
        fireEvent.change(fontSizeSlider, { target: { value: '18' } });
        expect(mockUpdateEditorPreferences).toHaveBeenCalledWith({
          fontSize: 18,
        });
      }
    });

    it('toggles word wrap', async () => {
      render(<Settings />);

      const wordWrapSwitch = screen.getByLabelText('Word Wrap');
      fireEvent.click(wordWrapSwitch);

      expect(mockUpdateEditorPreferences).toHaveBeenCalledWith({
        wordWrap: false,
      });
    });

    it('toggles spell check', async () => {
      render(<Settings />);

      const spellCheckSwitch = screen.getByLabelText('Spell Check');
      fireEvent.click(spellCheckSwitch);

      expect(mockUpdateEditorPreferences).toHaveBeenCalledWith({
        spellCheck: false,
      });
    });
  });

  describe('Password Change', () => {
    it('opens password change modal', async () => {
      render(<Settings />);

      const changePasswordButton = screen.getByText('Change Password');
      fireEvent.click(changePasswordButton);

      await waitFor(() => {
        expect(
          screen.getByRole('heading', { name: 'Change Password' })
        ).toBeInTheDocument();
      });

      expect(screen.getByLabelText('Current Password')).toBeInTheDocument();
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
      expect(screen.getByLabelText('Confirm New Password')).toBeInTheDocument();
    });

    it('successfully changes password', async () => {
      (api.changePassword as Mock).mockResolvedValue({
        message: 'Password changed successfully',
      });

      render(<Settings />);

      // Open modal
      fireEvent.click(screen.getByText('Change Password'));

      await waitFor(() => {
        expect(screen.getByLabelText('Current Password')).toBeInTheDocument();
      });

      // Fill form
      fireEvent.change(screen.getByLabelText('Current Password'), {
        target: { value: 'oldpass123' },
      });
      fireEvent.change(screen.getByLabelText('New Password'), {
        target: { value: 'newpass123' },
      });
      fireEvent.change(screen.getByLabelText('Confirm New Password'), {
        target: { value: 'newpass123' },
      });

      // Submit
      const submitButton = screen
        .getAllByText('Change Password')
        .find((btn) => btn.tagName === 'BUTTON');
      if (submitButton) {
        fireEvent.click(submitButton);
      }

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Password changed',
            status: 'success',
          })
        );
      });
    });

    it('shows error when passwords do not match', async () => {
      render(<Settings />);

      // Open modal
      fireEvent.click(screen.getByText('Change Password'));

      await waitFor(() => {
        expect(screen.getByLabelText('Current Password')).toBeInTheDocument();
      });

      // Fill form with mismatched passwords
      fireEvent.change(screen.getByLabelText('Current Password'), {
        target: { value: 'oldpass123' },
      });
      fireEvent.change(screen.getByLabelText('New Password'), {
        target: { value: 'newpass123' },
      });
      fireEvent.change(screen.getByLabelText('Confirm New Password'), {
        target: { value: 'differentpass' },
      });

      // Submit
      const submitButton = screen
        .getAllByText('Change Password')
        .find((btn) => btn.tagName === 'BUTTON');
      if (submitButton) {
        fireEvent.click(submitButton);
      }

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Passwords do not match',
            status: 'error',
          })
        );
      });
    });
  });

  describe('Export Notes', () => {
    it('exports notes successfully', async () => {
      const mockBlob = new Blob(['test'], { type: 'application/zip' });
      (api.exportNotes as Mock).mockResolvedValue(mockBlob);

      // Mock URL.createObjectURL and related methods
      global.URL.createObjectURL = vi.fn(() => 'mock-url');
      global.URL.revokeObjectURL = vi.fn();

      const mockClick = vi.fn();
      const mockAppendChild = vi.fn();
      const mockRemoveChild = vi.fn();

      vi.spyOn(document, 'createElement').mockImplementation((tag) => {
        const element = {
          tagName: tag.toUpperCase(),
          click: mockClick,
          href: '',
          download: '',
        } as unknown as HTMLElement;
        return element;
      });

      vi.spyOn(document.body, 'appendChild').mockImplementation(
        mockAppendChild
      );
      vi.spyOn(document.body, 'removeChild').mockImplementation(
        mockRemoveChild
      );

      render(<Settings />);

      const exportButton = screen.getByText('Export All Notes');
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Notes exported',
            status: 'success',
          })
        );
      });

      expect(mockClick).toHaveBeenCalled();
      expect(mockAppendChild).toHaveBeenCalled();
      expect(mockRemoveChild).toHaveBeenCalled();
    });
  });

  describe('Delete Account', () => {
    it('opens delete account modal', async () => {
      render(<Settings />);

      const deleteButton = screen.getByText('Delete Account');
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(
          screen.getByRole('heading', { name: 'Delete Account' })
        ).toBeInTheDocument();
      });

      expect(
        screen.getByText('This action cannot be undone!')
      ).toBeInTheDocument();
    });

    it('successfully deletes account and logs out', async () => {
      (api.deleteAccount as Mock).mockResolvedValue({
        message: 'Account deleted successfully',
      });

      render(<Settings />);

      // Open modal
      fireEvent.click(screen.getByText('Delete Account'));

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter your password')
        ).toBeInTheDocument();
      });

      // Enter password
      fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
        target: { value: 'testpass123' },
      });

      // Confirm deletion
      const confirmButton = screen.getByText('Delete My Account');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Account deleted',
            status: 'success',
          })
        );
      });

      expect(mockLogout).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  describe('Reset to Defaults', () => {
    it('resets all preferences to defaults', async () => {
      render(<Settings />);

      const resetButton = screen.getByText('Reset All Preferences to Defaults');
      fireEvent.click(resetButton);

      expect(mockResetToDefaults).toHaveBeenCalled();
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Settings reset',
            status: 'info',
          })
        );
      });
    });
  });
});
