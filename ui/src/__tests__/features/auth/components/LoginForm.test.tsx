import { vi, Mock } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { useNavigate, useLocation } from 'react-router-dom';
import { render } from '../../../../../test-utils/render';
import LoginForm from '../../../../features/auth/components/LoginForm';
import { useAuthStore } from '../../../../features/auth/store';
import {
  mockUnauthenticatedStore,
  mockAuthStoreWithError,
} from '../../../__mocks__/mockStores';

// Mock the zustand hook
vi.mock('../../../../features/auth/store');

// Mock react-router's useNavigate and useLocation
vi.mock('react-router-dom', async () => ({
  ...(await import('react-router-dom')),
  useNavigate: vi.fn(),
  useLocation: vi.fn(),
}));

describe('LoginForm', () => {
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useNavigate as Mock).mockReturnValue(mockNavigate);
    // Mock useLocation with default state
    (useLocation as Mock).mockReturnValue({
      pathname: '/login',
      state: null,
    });
    // Mock the auth store for direct access pattern
    (useAuthStore as Mock).mockReturnValue(mockUnauthenticatedStore);
  });

  it('renders the login form correctly', () => {
    render(<LoginForm />);

    expect(screen.getByText('Login to Parchmark')).toBeInTheDocument();
    expect(screen.getByTestId('username-input')).toBeInTheDocument();
    expect(screen.getByTestId('password-input')).toBeInTheDocument();
    expect(screen.getByTestId('login-button')).toBeInTheDocument();
  });

  it('shows validation errors when submitting empty form', async () => {
    render(<LoginForm />);

    const loginButton = screen.getByTestId('login-button');
    const form = loginButton.closest('form');

    // Submit the form by firing submit event on the form element
    fireEvent.submit(form!);

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText('Username is required')).toBeInTheDocument();
      expect(screen.getByText('Password is required')).toBeInTheDocument();
    });

    // Login should not be called
    expect(mockUnauthenticatedStore.actions.login).not.toHaveBeenCalled();
  });

  it('shows username validation error when only username is empty', async () => {
    render(<LoginForm />);

    // Fill only password
    fireEvent.change(screen.getByTestId('password-input'), {
      target: { value: 'password' },
    });

    const loginButton = screen.getByTestId('login-button');
    const form = loginButton.closest('form');

    // Submit the form
    fireEvent.submit(form!);

    // Should show only username validation error
    await waitFor(() => {
      expect(screen.getByText('Username is required')).toBeInTheDocument();
      expect(
        screen.queryByText('Password is required')
      ).not.toBeInTheDocument();
    });

    // Login should not be called
    expect(mockUnauthenticatedStore.actions.login).not.toHaveBeenCalled();
  });

  it('shows password validation error when only password is empty', async () => {
    render(<LoginForm />);

    // Fill only username
    fireEvent.change(screen.getByTestId('username-input'), {
      target: { value: 'user' },
    });

    const loginButton = screen.getByTestId('login-button');
    const form = loginButton.closest('form');

    // Submit the form
    fireEvent.submit(form!);

    // Should show only password validation error
    await waitFor(() => {
      expect(
        screen.queryByText('Username is required')
      ).not.toBeInTheDocument();
      expect(screen.getByText('Password is required')).toBeInTheDocument();
    });

    // Login should not be called
    expect(mockUnauthenticatedStore.actions.login).not.toHaveBeenCalled();
  });

  it('calls login action and redirects on successful login', async () => {
    // Mock successful login with direct access pattern
    const mockSuccessfulStore = {
      ...mockUnauthenticatedStore,
      actions: {
        ...mockUnauthenticatedStore.actions,
        login: vi.fn().mockReturnValue(true),
      },
    };
    (useAuthStore as Mock).mockReturnValue(mockSuccessfulStore);

    render(<LoginForm />);

    // Fill the form
    fireEvent.change(screen.getByTestId('username-input'), {
      target: { value: 'user' },
    });
    fireEvent.change(screen.getByTestId('password-input'), {
      target: { value: 'password' },
    });

    // Submit the form
    fireEvent.click(screen.getByTestId('login-button'));

    // Login should be called with correct values
    await waitFor(() => {
      expect(mockSuccessfulStore.actions.login).toHaveBeenCalledWith(
        'user',
        'password'
      );
      expect(mockNavigate).toHaveBeenCalledWith('/notes', { replace: true });
    });
  });

  it('shows error message on failed login', async () => {
    // Mock login with error
    (useAuthStore as Mock).mockReturnValue(mockAuthStoreWithError);

    render(<LoginForm />);

    // Error should be displayed
    expect(
      screen.getByText('Invalid username or password')
    ).toBeInTheDocument();
  });

  it('does not redirect on failed login', async () => {
    // Mock failed login with direct access pattern
    const mockFailedLoginStore = {
      ...mockUnauthenticatedStore,
      actions: {
        ...mockUnauthenticatedStore.actions,
        login: vi.fn().mockReturnValue(false),
      },
    };
    (useAuthStore as Mock).mockReturnValue(mockFailedLoginStore);

    render(<LoginForm />);

    // Fill the form
    fireEvent.change(screen.getByTestId('username-input'), {
      target: { value: 'user' },
    });
    fireEvent.change(screen.getByTestId('password-input'), {
      target: { value: 'wrongpassword' },
    });

    // Submit the form
    fireEvent.click(screen.getByTestId('login-button'));

    // Login should be called but navigate should not
    await waitFor(() => {
      expect(mockFailedLoginStore.actions.login).toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  it('redirects to custom location from state', async () => {
    const mockSuccessfulStore = {
      ...mockUnauthenticatedStore,
      actions: {
        ...mockUnauthenticatedStore.actions,
        login: vi.fn().mockReturnValue(true),
      },
    };
    (useAuthStore as Mock).mockReturnValue(mockSuccessfulStore);

    render(<LoginForm />, {
      routerOptions: {
        initialEntries: ['/login'],
        initialIndex: 0,
      },
    });

    // Mock location state with custom 'from' path
    (useLocation as Mock).mockReturnValue({
      state: { from: { pathname: '/custom-path' } },
    });

    // Fill and submit form
    fireEvent.change(screen.getByTestId('username-input'), {
      target: { value: 'user' },
    });
    fireEvent.change(screen.getByTestId('password-input'), {
      target: { value: 'password' },
    });
    fireEvent.click(screen.getByTestId('login-button'));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/custom-path', {
        replace: true,
      });
    });
  });

  it('toggles password visibility when clicking the toggle button', () => {
    render(<LoginForm />);

    const passwordInput = screen.getByTestId('password-input');
    const toggleButton = screen.getByTestId('password-toggle');

    // Initially, password should be hidden
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(toggleButton).toHaveAttribute('aria-label', 'Show password');

    // Click to show password
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(toggleButton).toHaveAttribute('aria-label', 'Hide password');

    // Click to hide password again
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(toggleButton).toHaveAttribute('aria-label', 'Show password');
  });

  it('preserves password value when toggling visibility', () => {
    render(<LoginForm />);

    const passwordInput = screen.getByTestId(
      'password-input'
    ) as HTMLInputElement;
    const toggleButton = screen.getByTestId('password-toggle');

    // Enter a password
    fireEvent.change(passwordInput, { target: { value: 'mySecretPassword' } });
    expect(passwordInput.value).toBe('mySecretPassword');

    // Toggle visibility - value should remain
    fireEvent.click(toggleButton);
    expect(passwordInput.value).toBe('mySecretPassword');
    expect(passwordInput).toHaveAttribute('type', 'text');

    // Toggle back - value should still remain
    fireEvent.click(toggleButton);
    expect(passwordInput.value).toBe('mySecretPassword');
    expect(passwordInput).toHaveAttribute('type', 'password');
  });
});
