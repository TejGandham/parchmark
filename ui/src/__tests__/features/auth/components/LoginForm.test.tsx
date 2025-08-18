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
jest.mock('../../../../features/auth/store');

// Mock react-router's useNavigate and useLocation
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
  useLocation: jest.fn(),
}));

describe('LoginForm', () => {
  const mockNavigate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
    // Mock the auth store for direct access pattern
    (useAuthStore as jest.Mock).mockReturnValue(mockUnauthenticatedStore);
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
        login: jest.fn().mockReturnValue(true),
      },
    };
    (useAuthStore as jest.Mock).mockReturnValue(mockSuccessfulStore);

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
    (useAuthStore as jest.Mock).mockReturnValue(mockAuthStoreWithError);

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
        login: jest.fn().mockReturnValue(false),
      },
    };
    (useAuthStore as jest.Mock).mockReturnValue(mockFailedLoginStore);

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
        login: jest.fn().mockReturnValue(true),
      },
    };
    (useAuthStore as jest.Mock).mockReturnValue(mockSuccessfulStore);

    render(<LoginForm />, {
      routerOptions: {
        initialEntries: ['/login'],
        initialIndex: 0,
      },
    });

    // Mock location state with custom 'from' path
    (useLocation as jest.Mock).mockReturnValue({
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
});
