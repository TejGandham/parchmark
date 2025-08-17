import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import LoginForm from '../../../../features/auth/components/LoginForm';
import { useAuthStore } from '../../../../features/auth/store';
import {
  mockAuthStore,
  mockUnauthenticatedStore,
  mockAuthStoreWithError,
} from '../../../__mocks__/mockStores';

// Mock the zustand hook
jest.mock('../../../../features/auth/store');

// Mock react-router's useNavigate
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
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
    render(
      <MemoryRouter>
        <LoginForm />
      </MemoryRouter>
    );

    expect(screen.getByText('Login to Parchmark')).toBeInTheDocument();
    expect(screen.getByTestId('username-input')).toBeInTheDocument();
    expect(screen.getByTestId('password-input')).toBeInTheDocument();
    expect(screen.getByTestId('login-button')).toBeInTheDocument();
  });

  it('does not call login when form is invalid', async () => {
    render(
      <MemoryRouter>
        <LoginForm />
      </MemoryRouter>
    );

    // Submit with empty fields
    fireEvent.click(screen.getByTestId('login-button'));

    // Login should not be called
    await waitFor(() => {
      expect(mockUnauthenticatedStore.actions.login).not.toHaveBeenCalled();
    });
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

    render(
      <MemoryRouter>
        <LoginForm />
      </MemoryRouter>
    );

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

    render(
      <MemoryRouter>
        <LoginForm />
      </MemoryRouter>
    );

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

    render(
      <MemoryRouter>
        <LoginForm />
      </MemoryRouter>
    );

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
});
