import { vi, Mock, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent, within } from '@testing-library/react';
import { act } from 'react';
import { render } from '../../../../../test-utils/render';
import Settings from '../../../../features/settings/components/Settings';
import { useAuthStore } from '../../../../features/auth/store';
import * as api from '../../../../services/api';

// Mock the API
vi.mock('../../../../services/api');

// Mock auth store
vi.mock('../../../../features/auth/store');

// Mock react-router's useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => ({
  ...(await vi.importActual('react-router-dom')),
  useNavigate: () => mockNavigate,
}));

// Mock toast
const mockToast = vi.fn();
vi.mock('@chakra-ui/react', async () => {
  const actual = await vi.importActual('@chakra-ui/react');
  return {
    ...actual,
    useToast: () => mockToast,
  };
});

describe('Settings Component', () => {
  const mockLogout = vi.fn();

  const defaultAuthStore = {
    user: { username: 'testuser', password: '' },
    actions: {
      logout: mockLogout,
    },
  };

  const mockUserInfo: api.UserInfo = {
    username: 'testuser',
    email: null,
    created_at: '2025-01-01T00:00:00Z',
    notes_count: 5,
    auth_provider: 'local',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as Mock).mockImplementation((selector) => {
      if (typeof selector === 'function') {
        return selector(defaultAuthStore);
      }
      return defaultAuthStore;
    });
    mockToast.mockClear();

    // Mock API calls
    (api.getUserInfo as Mock).mockResolvedValue(mockUserInfo);
    (api.changePassword as Mock).mockResolvedValue({
      message: 'Password changed successfully',
    });
    (api.deleteAccount as Mock).mockResolvedValue({
      message: 'Account deleted successfully',
    });
    (api.exportNotes as Mock).mockResolvedValue(
      new Blob(['test'], { type: 'application/zip' })
    );
  });

  describe('Rendering', () => {
    it('renders settings page with all sections', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(
          screen.getByRole('heading', { name: 'Settings' })
        ).toBeInTheDocument();
      });

      // Check for accordion sections (4 sections for local users)
      expect(screen.getByText('Profile Information')).toBeInTheDocument();
      expect(screen.getByText('Password & Security')).toBeInTheDocument();
      expect(screen.getByText('Data Management')).toBeInTheDocument();
      expect(screen.getByText('Danger Zone')).toBeInTheDocument();
    });

    it('loads and displays user info', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByDisplayValue('testuser')).toBeInTheDocument();
      });

      expect(screen.getByText('Total Notes')).toBeInTheDocument();
    });

    it('shows loading spinner while loading user info', async () => {
      // Make getUserInfo never resolve immediately
      (api.getUserInfo as Mock).mockImplementation(() => new Promise(() => {}));

      render(<Settings />);

      // Should show spinner (Chakra Spinner has class 'chakra-spinner')
      const spinner = document.querySelector('.chakra-spinner');
      expect(spinner).toBeInTheDocument();
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

  describe('OIDC User Handling', () => {
    it('hides password section for OIDC users', async () => {
      (api.getUserInfo as Mock).mockResolvedValue({
        ...mockUserInfo,
        auth_provider: 'oidc',
        email: 'user@example.com',
      });

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Password section should not be present for OIDC users
      expect(screen.queryByText('Password & Security')).not.toBeInTheDocument();

      // Should show SSO info alert
      expect(
        screen.getByText(/signed in via Single Sign-On/i)
      ).toBeInTheDocument();
    });

    it('shows email for OIDC users', async () => {
      (api.getUserInfo as Mock).mockResolvedValue({
        ...mockUserInfo,
        auth_provider: 'oidc',
        email: 'user@example.com',
      });

      render(<Settings />);

      await waitFor(() => {
        expect(
          screen.getByDisplayValue('user@example.com')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Back Navigation', () => {
    it('navigates back to notes when back button is clicked', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      const backButton = screen.getByLabelText('Back to notes');
      fireEvent.click(backButton);

      expect(mockNavigate).toHaveBeenCalledWith('/notes');
    });
  });

  describe('Export Notes', () => {
    it('exports notes successfully', async () => {
      // Mock URL.createObjectURL and URL.revokeObjectURL
      const mockCreateObjectURL = vi.fn(() => 'blob:test');
      const mockRevokeObjectURL = vi.fn();
      global.URL.createObjectURL = mockCreateObjectURL;
      global.URL.revokeObjectURL = mockRevokeObjectURL;

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
    });

    it('shows error toast when export fails', async () => {
      (api.exportNotes as Mock).mockRejectedValue(new Error('Export failed'));

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

    it('shows error when export result is empty', async () => {
      (api.exportNotes as Mock).mockResolvedValue(
        new Blob([], { type: 'application/zip' })
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

  describe('Password Change Modal', () => {
    const expandPasswordSection = async () => {
      // Expand Password & Security accordion
      const passwordSection = screen.getByText('Password & Security');
      await act(async () => {
        fireEvent.click(passwordSection);
      });
    };

    it('opens password modal when button is clicked', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      await expandPasswordSection();

      // Find and click Change Password button
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /change password/i })
        ).toBeInTheDocument();
      });

      const changePasswordButton = screen.getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(changePasswordButton);
      });

      // Modal should open
      await waitFor(() => {
        expect(screen.getByText('Current Password')).toBeInTheDocument();
        expect(screen.getByText('New Password')).toBeInTheDocument();
        expect(screen.getByText('Confirm New Password')).toBeInTheDocument();
      });
    });

    it('successfully changes password', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      await expandPasswordSection();

      // Open modal
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /change password/i })
        ).toBeInTheDocument();
      });

      const changePasswordButton = screen.getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(changePasswordButton);
      });

      // Fill form
      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter current password')
        ).toBeInTheDocument();
      });

      fireEvent.change(screen.getByPlaceholderText('Enter current password'), {
        target: { value: 'currentpass' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter new password'), {
        target: { value: 'newpass123' },
      });
      fireEvent.change(screen.getByPlaceholderText('Confirm new password'), {
        target: { value: 'newpass123' },
      });

      // Submit - find the modal and get its submit button
      const modal = screen.getByRole('dialog');
      const submitButton = within(modal).getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(api.changePassword).toHaveBeenCalledWith(
          'currentpass',
          'newpass123'
        );
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Password changed successfully',
            status: 'success',
          })
        );
      });
    });

    it('shows error when passwords do not match', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      await expandPasswordSection();

      // Open modal
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /change password/i })
        ).toBeInTheDocument();
      });

      const changePasswordButton = screen.getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(changePasswordButton);
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter current password')
        ).toBeInTheDocument();
      });

      // Fill form with mismatched passwords
      fireEvent.change(screen.getByPlaceholderText('Enter current password'), {
        target: { value: 'currentpass' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter new password'), {
        target: { value: 'newpass123' },
      });
      fireEvent.change(screen.getByPlaceholderText('Confirm new password'), {
        target: { value: 'different123' },
      });

      // Submit - find the modal and get its submit button
      const modal = screen.getByRole('dialog');
      const submitButton = within(modal).getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Passwords do not match',
            status: 'error',
          })
        );
      });
    });

    it('shows error when password is too short', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      await expandPasswordSection();

      // Open modal
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /change password/i })
        ).toBeInTheDocument();
      });

      const changePasswordButton = screen.getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(changePasswordButton);
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter current password')
        ).toBeInTheDocument();
      });

      // Fill form with short password
      fireEvent.change(screen.getByPlaceholderText('Enter current password'), {
        target: { value: 'currentpass' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter new password'), {
        target: { value: 'abc' },
      });
      fireEvent.change(screen.getByPlaceholderText('Confirm new password'), {
        target: { value: 'abc' },
      });

      // Submit - find the modal and get its submit button
      const modal = screen.getByRole('dialog');
      const submitButton = within(modal).getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Password too short',
            status: 'error',
          })
        );
      });
    });

    it('shows error when password change fails', async () => {
      (api.changePassword as Mock).mockRejectedValue(
        new Error('Current password is incorrect')
      );

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      await expandPasswordSection();

      // Open modal
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /change password/i })
        ).toBeInTheDocument();
      });

      const changePasswordButton = screen.getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(changePasswordButton);
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText('Enter current password')
        ).toBeInTheDocument();
      });

      // Fill form
      fireEvent.change(screen.getByPlaceholderText('Enter current password'), {
        target: { value: 'wrongpass' },
      });
      fireEvent.change(screen.getByPlaceholderText('Enter new password'), {
        target: { value: 'newpass123' },
      });
      fireEvent.change(screen.getByPlaceholderText('Confirm new password'), {
        target: { value: 'newpass123' },
      });

      // Submit - find the modal and get its submit button
      const modal = screen.getByRole('dialog');
      const submitButton = within(modal).getByRole('button', {
        name: /change password/i,
      });
      await act(async () => {
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Failed to change password',
            status: 'error',
          })
        );
      });
    });
  });

  describe('Delete Account Modal', () => {
    it('opens delete modal when button is clicked', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand Danger Zone accordion first
      const dangerZoneButton = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerZoneButton);
      });

      // Find and click Delete Account button
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /delete account/i })
        ).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', {
        name: /delete account/i,
      });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      // Modal should open
      await waitFor(() => {
        expect(
          screen.getByText(/This action is irreversible/i)
        ).toBeInTheDocument();
        expect(screen.getByPlaceholderText('DELETE')).toBeInTheDocument();
      });
    });

    it('successfully deletes account', async () => {
      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });

      // Expand Danger Zone accordion
      const dangerZoneButton = screen.getByText('Danger Zone');
      await act(async () => {
        fireEvent.click(dangerZoneButton);
      });

      // Open modal
      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /delete account/i })
        ).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', {
        name: /delete account/i,
      });
      await act(async () => {
        fireEvent.click(deleteButton);
      });

      await waitFor(() => {
        expect(screen.getByPlaceholderText('DELETE')).toBeInTheDocument();
      });

      // Fill form correctly
      fireEvent.change(screen.getByPlaceholderText('Enter your password'), {
        target: { value: 'password123' },
      });
      fireEvent.change(screen.getByPlaceholderText('DELETE'), {
        target: { value: 'DELETE' },
      });

      // Submit
      const submitButtons = screen.getAllByRole('button', {
        name: /delete account/i,
      });
      const modalSubmitButton = submitButtons[submitButtons.length - 1];
      await act(async () => {
        fireEvent.click(modalSubmitButton);
      });

      await waitFor(() => {
        expect(api.deleteAccount).toHaveBeenCalledWith('password123');
        expect(mockLogout).toHaveBeenCalled();
        expect(mockNavigate).toHaveBeenCalledWith('/login');
      });
    });
  });
});
