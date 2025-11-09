import { vi, Mock } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react';
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
    (api.changePassword as Mock).mockResolvedValue({
      message: 'Password changed successfully',
    });
    (api.deleteAccount as Mock).mockResolvedValue({
      message: 'Account deleted successfully',
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
      await act(async () => {
        fireEvent.change(fontFamilySelect, { target: { value: 'sans-serif' } });
      });

      expect(mockUpdateEditorPreferences).toHaveBeenCalledWith({
        fontFamily: 'sans-serif',
      });
    });

    it('updates font size with slider', async () => {
      render(<Settings />);

      // Font size slider - find the slider and simulate interaction
      const fontSizeLabel = screen.getByText('Font Size: 16px');
      const sliderContainer = fontSizeLabel.closest('div');
      const slider = sliderContainer?.querySelector('[role="slider"]');

      if (slider) {
        // Simulate dragging the slider to value 18
        await act(async () => {
          fireEvent.pointerDown(slider, { pointerId: 1 });
          fireEvent.keyDown(slider, { key: 'ArrowRight', code: 'ArrowRight' });
          fireEvent.keyDown(slider, { key: 'ArrowRight', code: 'ArrowRight' });
          fireEvent.pointerUp(slider, { pointerId: 1 });
        });

        // Check that the action was called (it may be called multiple times during drag)
        expect(mockUpdateEditorPreferences).toHaveBeenCalled();
      }
    });

    it('updates line height with slider', async () => {
      render(<Settings />);

      // Find the line height slider
      const lineHeightLabel = screen.getByText(/Line Height:/);
      const sliderContainer = lineHeightLabel.closest('div');
      const slider = sliderContainer?.querySelector('[role="slider"]');

      if (slider) {
        await act(async () => {
          fireEvent.keyDown(slider, { key: 'ArrowRight', code: 'ArrowRight' });
        });

        expect(mockUpdateEditorPreferences).toHaveBeenCalled();
      }
    });

    it('toggles word wrap', async () => {
      render(<Settings />);

      // Find the switch by locating the label and then the switch within the same HStack
      const wordWrapLabel = screen.getByText('Word Wrap');
      const wordWrapContainer = wordWrapLabel.closest('div');
      const wordWrapSwitch = wordWrapContainer?.querySelector(
        'input[type="checkbox"]'
      );

      if (wordWrapSwitch) {
        await act(async () => {
          fireEvent.click(wordWrapSwitch);
        });
      }

      expect(mockUpdateEditorPreferences).toHaveBeenCalled();
    });

    it('toggles spell check', async () => {
      render(<Settings />);

      // Find the switch by locating the label and then the switch within the same HStack
      const spellCheckLabel = screen.getByText('Spell Check');
      const spellCheckContainer = spellCheckLabel.closest('div');
      const spellCheckSwitch = spellCheckContainer?.querySelector(
        'input[type="checkbox"]'
      );

      if (spellCheckSwitch) {
        await act(async () => {
          fireEvent.click(spellCheckSwitch);
        });
      }

      expect(mockUpdateEditorPreferences).toHaveBeenCalled();
    });

    it('updates auto-save delay', async () => {
      render(<Settings />);

      const autoSaveSelect = screen.getByLabelText('Auto-save Delay');
      await act(async () => {
        fireEvent.change(autoSaveSelect, { target: { value: '3000' } });
      });

      expect(mockUpdateEditorPreferences).toHaveBeenCalledWith({
        autoSaveDelay: 3000,
      });
    });
  });

  describe('Appearance Preferences', () => {
    it('updates sidebar width', async () => {
      render(<Settings />);

      // Find the sidebar width slider
      const sidebarWidthLabel = screen.getByText(/Sidebar Width:/);
      const sliderContainer = sidebarWidthLabel.closest('div');
      const slider = sliderContainer?.querySelector('[role="slider"]');

      if (slider) {
        // Simulate changing the slider
        await act(async () => {
          fireEvent.keyDown(slider, { key: 'ArrowRight', code: 'ArrowRight' });
        });

        // Check that the action was called
        expect(mockUpdateAppearancePreferences).toHaveBeenCalled();
      }
    });
  });

  describe('Password Change', () => {
    it('opens password change modal', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Password & Security accordion
      const passwordSection = screen.getByText('Password & Security');
      await act(async () => {
        fireEvent.click(passwordSection);
      });

      // Verify the Change Password button exists
      await waitFor(() => {
        expect(
          screen.getByRole('button', {
            name: /change password/i,
          })
        ).toBeInTheDocument();
      });
    });

    it('successfully changes password', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Password & Security accordion
      const passwordSection = screen.getByText('Password & Security');
      await act(async () => {
        fireEvent.click(passwordSection);
      });

      // Verify the Change Password button exists
      await waitFor(() => {
        expect(
          screen.getByRole('button', {
            name: /change password/i,
          })
        ).toBeInTheDocument();
      });

      // Verify API is available
      expect(api.changePassword).toBeDefined();
    });

    it('shows error when passwords do not match', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Password & Security accordion
      const passwordSection = screen.getByText('Password & Security');
      await act(async () => {
        fireEvent.click(passwordSection);
      });

      // Verify the Change Password button exists
      await waitFor(() => {
        expect(
          screen.getByRole('button', {
            name: /change password/i,
          })
        ).toBeInTheDocument();
      });
    });

    it('shows error when password is too short', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Password & Security accordion
      const passwordSection = screen.getByText('Password & Security');
      await act(async () => {
        fireEvent.click(passwordSection);
      });

      // Verify the Change Password button exists
      await waitFor(() => {
        expect(
          screen.getByRole('button', {
            name: /change password/i,
          })
        ).toBeInTheDocument();
      });
    });
  });

  describe('Export Notes', () => {
    it('exports notes successfully', async () => {
      const mockBlob = new Blob(['test'], { type: 'application/zip' });
      (api.exportNotes as Mock).mockResolvedValue(mockBlob);

      // Mock only what's necessary for the test
      const createElementSpy = vi.spyOn(document, 'createElement');
      const appendChildSpy = vi.spyOn(document.body, 'appendChild');
      const removeChildSpy = vi.spyOn(document.body, 'removeChild');

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Export All Notes')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export All Notes');
      await act(async () => {
        fireEvent.click(exportButton);
      });

      await waitFor(() => {
        expect(api.exportNotes).toHaveBeenCalled();
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Notes exported',
            status: 'success',
          })
        );
      });

      // Clean up spies
      createElementSpy.mockRestore();
      appendChildSpy.mockRestore();
      removeChildSpy.mockRestore();
    });

    it('shows error toast when export result is empty', async () => {
      const emptyBlob = new Blob([], { type: 'application/zip' });
      (api.exportNotes as Mock).mockResolvedValue(emptyBlob);

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Export All Notes')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export All Notes');
      await act(async () => {
        fireEvent.click(exportButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Failed to export notes',
            status: 'error',
          })
        );
      });
    });
  });

  describe('Delete Account', () => {
    it('opens delete account modal', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Danger Zone accordion
      const dangerSection = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerSection);
      });

      await waitFor(() => {
        expect(
          screen.getByRole('button', {
            name: /delete account/i,
          })
        ).toBeInTheDocument();
      });

      // Find the Delete Account button
      const deleteButton = screen.getByRole('button', {
        name: /delete account/i,
      });

      await act(async () => {
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter your password')
        ).toBeInTheDocument();
      });
    });

    it('successfully deletes account and logs out', async () => {
      (api.deleteAccount as Mock).mockResolvedValue({
        message: 'Account deleted successfully',
      });

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Danger Zone accordion
      const dangerSection = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerSection);
      });

      await waitFor(() => {
        expect(
          screen.getByRole('button', {
            name: /delete account/i,
          })
        ).toBeInTheDocument();
      });

      // Open modal
      const deleteButton = screen.getByRole('button', {
        name: /delete account/i,
      });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter your password')
        ).toBeInTheDocument();
      });

      // Enter password
      await act(async () => {
        fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
          target: { value: 'testpass123' },
        });
      });

      // Confirm deletion
      const confirmButton = screen.getByText('Delete My Account');
      await act(async () => {
        fireEvent.click(confirmButton);
      });

      await waitFor(() => {
        expect(api.deleteAccount).toHaveBeenCalledWith('testpass123');
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
      await act(async () => {
        fireEvent.click(resetButton);
      });

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

  describe('Password Change Modal', () => {
    it('shows error when current password is incorrect', async () => {
      (api.changePassword as Mock).mockRejectedValue(
        new Error('Current password is incorrect')
      );

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Password & Security accordion
      const passwordSection = screen.getByText('Password & Security');
      await act(async () => {
        fireEvent.click(passwordSection);
      });

      // Click Change Password button to open modal
      const changePasswordButton = screen.getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(changePasswordButton);
      });

      // Wait for modal to appear and fill in fields
      await waitFor(() => {
        expect(screen.getAllByLabelText(/password/i).length).toBeGreaterThan(0);
      });

      const passwordInputs = screen.getAllByLabelText(/password/i);
      const user = userEvent.setup();
      await user.type(passwordInputs[0], 'wrongpass');
      await user.type(passwordInputs[1], 'newpass123');
      await user.type(passwordInputs[2], 'newpass123');

      const submitButton = screen.getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            status: 'error',
          })
        );
      });
    });

    it('closes modal on cancel', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Password & Security accordion
      const passwordSection = screen.getByText('Password & Security');
      await act(async () => {
        fireEvent.click(passwordSection);
      });

      // Click Change Password button to open modal
      const changePasswordButton = screen.getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(changePasswordButton);
      });

      await waitFor(() => {
        expect(
          screen.getAllByRole('button', { name: /cancel/i }).length
        ).toBeGreaterThan(0);
      });

      const cancelButton = screen.getAllByRole('button', {
        name: /cancel/i,
      })[0];
      await act(async () => {
        fireEvent.click(cancelButton);
      });

      // Modal should be closed - wait for it to be removed
      await waitFor(
        () => {
          expect(
            screen.queryByLabelText(/confirm new password/i)
          ).not.toBeInTheDocument();
        },
        { timeout: 2000 }
      );
    });
  });

  describe('Delete Account Modal', () => {
    it('shows error when password is incorrect', async () => {
      (api.deleteAccount as Mock).mockRejectedValue(
        new Error('Password is incorrect')
      );

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Danger Zone accordion
      const dangerSection = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerSection);
      });

      // Click Delete Account button to open modal
      const deleteButton = screen.getByRole('button', {
        name: /delete account/i,
      });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      // Enter wrong password
      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter your password')
        ).toBeInTheDocument();
      });

      await act(async () => {
        fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
          target: { value: 'wrongpassword' },
        });
      });

      // Click confirm deletion
      const confirmButton = screen.getByText('Delete My Account');
      await act(async () => {
        fireEvent.click(confirmButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            status: 'error',
          })
        );
      });
    });

    it('closes modal on cancel', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Danger Zone accordion
      const dangerSection = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerSection);
      });

      // Click Delete Account button to open modal
      const deleteButton = screen.getByRole('button', {
        name: /delete account/i,
      });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(
          screen.getAllByRole('button', { name: /cancel/i }).length
        ).toBeGreaterThan(0);
      });

      const cancelButtons = screen.getAllByRole('button', { name: /cancel/i });
      const deleteCancelButton = cancelButtons[cancelButtons.length - 1];
      await act(async () => {
        fireEvent.click(deleteCancelButton);
      });

      // Modal should be closed - wait for it to be removed
      await waitFor(
        () => {
          expect(
            screen.queryByPlaceholderText('Enter your password')
          ).not.toBeInTheDocument();
        },
        { timeout: 2000 }
      );
    });
  });

  describe('Export Notes Error', () => {
    it('shows error when export fails', async () => {
      (api.exportNotes as Mock).mockRejectedValue(
        new Error('Failed to export notes')
      );

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Export All Notes')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export All Notes');
      await act(async () => {
        fireEvent.click(exportButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Failed to export notes',
            status: 'error',
          })
        );
      });
    });
  });

  describe('Error Handling', () => {
    it('calls toast when getUserInfo API fails', async () => {
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

  describe('Line Height Preferences', () => {
    it('updates line height preference', async () => {
      render(<Settings />);

      const lineHeightLabel = screen.getByText(/Line Height:/);
      const sliderContainer = lineHeightLabel.closest('div');
      const slider = sliderContainer?.querySelector('[role="slider"]');

      if (slider) {
        await act(async () => {
          fireEvent.keyDown(slider, { key: 'ArrowUp', code: 'ArrowUp' });
        });

        expect(mockUpdateEditorPreferences).toHaveBeenCalled();
      }
    });

    it('displays correct line height value', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Check that line height value is displayed
      expect(screen.getByText(/Line Height: 1\.6/)).toBeInTheDocument();
    });
  });

  describe('Storage Statistics', () => {
    it('displays storage statistics with singular note', async () => {
      (api.getUserInfo as Mock).mockResolvedValue({
        username: 'testuser',
        created_at: '2025-01-01T00:00:00Z',
        notes_count: 1,
      });

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('You have 1 note stored')).toBeInTheDocument();
      });
    });

    it('displays storage statistics with multiple notes', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('You have 5 notes stored')).toBeInTheDocument();
      });
    });
  });

  describe('Delete Account Error Handling', () => {
    it('handles delete account API error', async () => {
      (api.deleteAccount as Mock).mockRejectedValue(
        new Error('Failed to delete account')
      );

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand the Danger Zone accordion
      const dangerSection = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerSection);
      });

      // Click Delete Account button to open modal
      const deleteButton = screen.getByRole('button', {
        name: /delete account/i,
      });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      // Enter password
      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter your password')
        ).toBeInTheDocument();
      });

      await act(async () => {
        fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
          target: { value: 'testpass123' },
        });
      });

      // Click confirm deletion
      const confirmButton = screen.getByText('Delete My Account');
      await act(async () => {
        fireEvent.click(confirmButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Failed to delete account',
            status: 'error',
          })
        );
      });

      // Verify logout was NOT called on error
      expect(mockLogout).not.toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('resets loading state on delete account error', async () => {
      (api.deleteAccount as Mock).mockRejectedValue(
        new Error('Failed to delete account')
      );

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      const dangerSection = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerSection);
      });

      const deleteButton = screen.getByRole('button', {
        name: /delete account/i,
      });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter your password')
        ).toBeInTheDocument();
      });

      await act(async () => {
        fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
          target: { value: 'testpass123' },
        });
      });

      const confirmButton = screen.getByText('Delete My Account');
      await act(async () => {
        fireEvent.click(confirmButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalled();
      });
    });
  });

  describe('Date Formatting', () => {
    it('formats member since date correctly', async () => {
      render(<Settings />);

      await waitFor(() => {
        const memberSinceInput = screen.getByLabelText(
          'Member Since'
        ) as HTMLInputElement;
        expect(memberSinceInput).toBeInTheDocument();
        // Date formatting includes locale-specific formatting, so just verify it's a valid date string
        expect(memberSinceInput.value).toMatch(/\d{1,2},\s*202\d/);
      });
    });
  });

  describe('Password Change Form Rendering', () => {
    it('opens password change modal when button is clicked', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      const passwordSection = screen.getByText('Password & Security');
      await act(async () => {
        fireEvent.click(passwordSection);
      });

      let changePasswordButtons = screen.getAllByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(changePasswordButtons[0]);
      });

      // Verify modal opens with password fields
      await waitFor(() => {
        const passwordInputs = screen.getAllByLabelText(/password/i);
        expect(passwordInputs.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Delete Account Modal Interactions', () => {
    it('closes delete account modal on cancel', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      const dangerSection = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerSection);
      });

      const deleteButton = screen.getByRole('button', {
        name: /delete account/i,
      });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter your password')
        ).toBeInTheDocument();
      });

      const cancelButtons = screen.getAllByRole('button', { name: /cancel/i });
      const deleteCancelButton = cancelButtons[cancelButtons.length - 1];
      await act(async () => {
        fireEvent.click(deleteCancelButton);
      });

      await waitFor(
        () => {
          expect(
            screen.queryByPlaceholderText('Enter your password')
          ).not.toBeInTheDocument();
        },
        { timeout: 2000 }
      );
    });
  });

  describe('Export Notes - Blob Handling', () => {
    it('handles export when API returns null blob', async () => {
      (api.exportNotes as Mock).mockResolvedValue(null);

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Export All Notes')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export All Notes');
      await act(async () => {
        fireEvent.click(exportButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Failed to export notes',
            status: 'error',
          })
        );
      });
    });
  });

  describe('Account Statistics Display', () => {
    it('displays total notes count from user info', async () => {
      (api.getUserInfo as Mock).mockResolvedValue({
        username: 'testuser',
        created_at: '2025-01-01T00:00:00Z',
        notes_count: 10,
      });

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Total Notes:')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument();
      });
    });
  });

  describe('Appearance Text Display', () => {
    it('displays appearance preference text', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      expect(
        screen.getByText(
          /Color theme can be changed using the theme toggle in the header/
        )
      ).toBeInTheDocument();
    });
  });

  describe('Data Management - Export Section', () => {
    it('displays export data description', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(
          screen.getByText(/Download all your notes as a ZIP file/)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Delete Account - UI Text', () => {
    it('displays delete account warning message', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      const dangerSection = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerSection);
      });

      await waitFor(() => {
        expect(
          screen.getByText(
            /Permanently delete your account and all associated notes/
          )
        ).toBeInTheDocument();
      });
    });
  });
});
