import React from 'react';
import { screen } from '@testing-library/react';
import { render } from '../../../../../../test-utils/render';
import UserInfo from '../../../../../features/auth/components/UserLoginStatus/UserInfo';
import { useAuthStore } from '../../../../../features/auth/store';

// Mock useBreakpointValue hook
jest.mock('@chakra-ui/react', () => ({
  ...jest.requireActual('@chakra-ui/react'),
  useBreakpointValue: jest.fn().mockReturnValue(true),
}));

// Mock the auth store
jest.mock('../../../../../features/auth/store');

describe('UserInfo', () => {
  it('should return null when user is not provided', () => {
    // Mock the store to return null user
    (useAuthStore as jest.Mock).mockImplementation((selector) => {
      const state = {
        user: null,
      };
      return selector(state);
    });

    const { container } = render(<UserInfo />);

    // UserInfo returns null, but ChakraProvider adds a hidden span
    // Check that no actual UI elements are rendered
    expect(container.querySelector('[role="button"]')).toBeNull();
    expect(container.querySelector('[role="menu"]')).toBeNull();
  });

  it('should render user info when user is provided', () => {
    const mockUser = { username: 'testuser', password: '' };

    // Mock the store to return a user
    (useAuthStore as jest.Mock).mockImplementation((selector) => {
      const state = {
        user: mockUser,
      };
      return selector(state);
    });

    render(<UserInfo />);

    const userButton = screen.getByRole('button', {
      name: /user menu for testuser/i,
    });
    expect(userButton).toBeInTheDocument();
  });
});
