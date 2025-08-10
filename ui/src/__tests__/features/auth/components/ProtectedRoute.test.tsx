import React from 'react';
import { render } from '@testing-library/react';
import { useAuthStore } from '../../../../features/auth/store';
import {
  mockAuthStore,
  mockUnauthenticatedStore,
} from '../../../__mocks__/mockStores';

// Mock the auth store
jest.mock('../../../../features/auth/store');

// Add a basic mock for Navigate
jest.mock('react-router-dom', () => ({
  Navigate: () => <div data-testid="navigate-mock">Navigate Mock</div>,
}));

// Import the component after mocks
import ProtectedRoute from '../../../../features/auth/components/ProtectedRoute';

describe('ProtectedRoute', () => {
  it('renders without errors', () => {
    // This is a simple test to verify the component renders without errors
    (useAuthStore as jest.Mock).mockReturnValue(mockAuthStore);

    expect(() => {
      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );
    }).not.toThrow();
  });
});
