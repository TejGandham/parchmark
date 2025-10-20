import { vi, Mock } from 'vitest';
import React from 'react';
import { render } from '@testing-library/react';
import { useAuthStore } from '../../../../features/auth/store';
import {
  mockAuthStore,
  mockUnauthenticatedStore,
} from '../../../__mocks__/mockStores';

// Mock the auth store
vi.mock('../../../../features/auth/store');

// Add a basic mock for Navigate
vi.mock('react-router-dom', () => ({
  Navigate: () => <div data-testid="navigate-mock">Navigate Mock</div>,
  useLocation: () => ({ pathname: '/protected' }),
}));

// Import the component after mocks
import ProtectedRoute from '../../../../features/auth/components/ProtectedRoute';

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders protected content when user is authenticated', () => {
    (useAuthStore as Mock).mockImplementation((selector) =>
      selector ? selector(mockAuthStore) : mockAuthStore
    );

    const { getByText } = render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects to login when user is not authenticated', () => {
    (useAuthStore as Mock).mockImplementation((selector) =>
      selector ? selector(mockUnauthenticatedStore) : mockUnauthenticatedStore
    );

    const { getByTestId } = render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(getByTestId('navigate-mock')).toBeInTheDocument();
  });

  it('handles edge case with undefined authentication state', () => {
    const undefinedAuthStore = {
      isAuthenticated: undefined,
      user: null,
      error: null,
      actions: mockUnauthenticatedStore.actions,
    };

    (useAuthStore as Mock).mockImplementation((selector) =>
      selector ? selector(undefinedAuthStore) : undefinedAuthStore
    );

    const { getByTestId } = render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    // Should redirect when isAuthenticated is falsy
    expect(getByTestId('navigate-mock')).toBeInTheDocument();
  });

  it('renders without errors when children is null', () => {
    (useAuthStore as Mock).mockImplementation((selector) =>
      selector ? selector(mockAuthStore) : mockAuthStore
    );

    expect(() => {
      render(<ProtectedRoute>{null}</ProtectedRoute>);
    }).not.toThrow();
  });
});
