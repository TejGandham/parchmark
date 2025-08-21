import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ChakraProvider } from '@chakra-ui/react';
import UserLoginStatus from '../../../../features/auth/components/UserLoginStatus/UserLoginStatus';
import { useAuthStore } from '../../../../features/auth/store';
import { mockBreakpoint } from '../../../__mocks__/testUtils';

// Mock the auth store
jest.mock('../../../../features/auth/store', () => ({
  useAuthStore: jest.fn(),
}));

const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;

// Mock navigate function
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock useBreakpointValue hook
const mockUseBreakpointValue = jest.fn();
jest.mock('@chakra-ui/react', () => {
  const actual = jest.requireActual('@chakra-ui/react');
  return {
    ...actual,
    useBreakpointValue: (...args: any[]) => mockUseBreakpointValue(...args),
  };
});

const renderWithProviders = (component: React.ReactNode) => {
  return render(
    <ChakraProvider>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </ChakraProvider>
  );
};

describe('UserLoginStatus', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseBreakpointValue.mockReturnValue(true); // Default to desktop view
  });

  describe('when user is not authenticated', () => {
    beforeEach(() => {
      mockUseAuthStore.mockReturnValue(false);
    });

    it('should render Sign In button', () => {
      renderWithProviders(<UserLoginStatus />);
      
      const signInButton = screen.getByRole('button', { name: /sign in to your account/i });
      expect(signInButton).toBeInTheDocument();
      expect(signInButton).toHaveTextContent('Sign In');
    });

    it('should navigate to /login when Sign In button is clicked', () => {
      renderWithProviders(<UserLoginStatus />);
      
      const signInButton = screen.getByRole('button', { name: /sign in to your account/i });
      fireEvent.click(signInButton);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  describe('when user is authenticated', () => {
    const mockLogout = jest.fn();
    const mockUser = { username: 'testuser', password: '' };

    beforeEach(() => {
      // Mock the selector function calls
      mockUseAuthStore.mockImplementation((selector) => {
        const state = { 
          isAuthenticated: true, 
          user: mockUser, 
          actions: { logout: mockLogout } 
        };
        return selector(state);
      });
    });

    it('should render user info with avatar', () => {
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      expect(userButton).toBeInTheDocument();
    });

    it('should show username on desktop breakpoint', () => {
      mockUseBreakpointValue.mockReturnValue(true); // Show username on desktop
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      expect(userButton).toBeInTheDocument();
      expect(userButton).toHaveTextContent('testuser');
    });

    it('should hide username on mobile breakpoint', () => {
      mockUseBreakpointValue.mockReturnValue(false); // Hide username on mobile
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      expect(userButton).toBeInTheDocument();
      expect(userButton).not.toHaveTextContent('testuser');
    });

    it('should show avatar with user initials', () => {
      mockUseBreakpointValue.mockReturnValue(true);
      renderWithProviders(<UserLoginStatus />);
      
      // Look for the first letter of 'testuser' since that's what the Avatar shows
      const avatar = screen.getByText('T');
      expect(avatar).toBeInTheDocument();
    });

    it('should open dropdown when user info is clicked', async () => {
      const user = userEvent.setup();
      mockUseBreakpointValue.mockReturnValue(true);
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      await user.click(userButton);
      
      await waitFor(() => {
        const dropdown = screen.getByRole('menu', { name: /user menu options/i });
        expect(dropdown).toBeInTheDocument();
      });
    });

    it('should close dropdown when clicked outside', async () => {
      const user = userEvent.setup();
      mockUseBreakpointValue.mockReturnValue(true);
      renderWithProviders(
        <div>
          <UserLoginStatus />
          <div data-testid="outside">Outside content</div>
        </div>
      );
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      await user.click(userButton);
      
      // Dropdown should open
      await waitFor(() => {
        expect(screen.getByRole('menu', { name: /user menu options/i })).toBeInTheDocument();
      });
      
      // Click outside
      const outsideElement = screen.getByTestId('outside');
      await user.click(outsideElement);
      
      // Dropdown should close
      await waitFor(() => {
        expect(screen.queryByRole('menu', { name: /user menu options/i })).not.toBeInTheDocument();
      });
    });

    it('should handle keyboard navigation to toggle dropdown', async () => {
      const user = userEvent.setup();
      mockUseBreakpointValue.mockReturnValue(true);
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      
      // Focus and press Enter
      await user.tab(); // Focus the button
      expect(userButton).toHaveFocus();
      
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        const dropdown = screen.getByRole('menu', { name: /user menu options/i });
        expect(dropdown).toBeInTheDocument();
      });
    });

    it('should handle logout from dropdown', async () => {
      const user = userEvent.setup();
      mockUseBreakpointValue.mockReturnValue(true);
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      await user.click(userButton);
      
      await waitFor(() => {
        const dropdown = screen.getByRole('menu', { name: /user menu options/i });
        expect(dropdown).toBeInTheDocument();
      });
      
      const logoutButton = screen.getByRole('menuitem', { name: /logout/i });
      await user.click(logoutButton);
      
      expect(mockLogout).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });

    it('should truncate long usernames', () => {
      const longUsername = 'verylongusername123';
      mockUseAuthStore.mockImplementation((selector) => {
        const state = { 
          isAuthenticated: true, 
          user: { username: longUsername, password: '' }, 
          actions: { logout: mockLogout } 
        };
        return selector(state);
      });
      
      mockUseBreakpointValue.mockReturnValue(true); // Show username on desktop
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: new RegExp(longUsername) });
      expect(userButton).toHaveTextContent('verylonguser...');
    });
  });

  describe('dropdown menu', () => {
    const mockLogout = jest.fn();
    const mockUser = { username: 'testuser', password: '' };

    beforeEach(() => {
      mockUseAuthStore.mockImplementation((selector) => {
        const state = { 
          isAuthenticated: true, 
          user: mockUser, 
          actions: { logout: mockLogout } 
        };
        return selector(state);
      });
    });

    it('should display all menu items when dropdown is open', async () => {
      const user = userEvent.setup();
      mockUseBreakpointValue.mockReturnValue(true);
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      await user.click(userButton);
      
      await waitFor(() => {
        expect(screen.getByRole('menuitem', { name: /profile/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /settings/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /help & support/i })).toBeInTheDocument();
        expect(screen.getByRole('menuitem', { name: /logout/i })).toBeInTheDocument();
      });
    });

    it('should show user info in dropdown header', async () => {
      const user = userEvent.setup();
      mockUseBreakpointValue.mockReturnValue(true);
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      await user.click(userButton);
      
      await waitFor(() => {
        expect(screen.getByText('Signed in as')).toBeInTheDocument();
        expect(screen.getAllByText('testuser')).toHaveLength(2); // One in button, one in dropdown
      });
    });

    it('should handle escape key to close dropdown', async () => {
      const user = userEvent.setup();
      mockUseBreakpointValue.mockReturnValue(true);
      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      await user.click(userButton);
      
      // Dropdown should open
      await waitFor(() => {
        expect(screen.getByRole('menu', { name: /user menu options/i })).toBeInTheDocument();
      });
      
      // Press escape
      await user.keyboard('{Escape}');
      
      // Dropdown should close
      await waitFor(() => {
        expect(screen.queryByRole('menu', { name: /user menu options/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('accessibility', () => {
    beforeEach(() => {
      mockUseBreakpointValue.mockReturnValue(true);
    });

    it('should have proper ARIA labels when logged out', () => {
      mockUseAuthStore.mockReturnValue(false);
      
      renderWithProviders(<UserLoginStatus />);
      
      const region = screen.getByRole('region', { name: /user authentication status/i });
      expect(region).toBeInTheDocument();
      
      const signInButton = screen.getByRole('button', { name: /sign in to your account/i });
      expect(signInButton).toBeInTheDocument();
    });

    it('should have proper ARIA labels when logged in', () => {
      const mockUser = { username: 'testuser', password: '' };
      mockUseAuthStore.mockImplementation((selector) => {
        const state = { 
          isAuthenticated: true, 
          user: mockUser, 
          actions: { logout: jest.fn() } 
        };
        return selector(state);
      });

      renderWithProviders(<UserLoginStatus />);
      
      const region = screen.getByRole('region', { name: /user authentication status/i });
      expect(region).toBeInTheDocument();
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      expect(userButton).toBeInTheDocument();
      expect(userButton).toHaveAttribute('aria-expanded', 'false');
      expect(userButton).toHaveAttribute('aria-haspopup', 'menu');
    });

    it('should update aria-expanded when dropdown opens', async () => {
      const user = userEvent.setup();
      const mockUser = { username: 'testuser', password: '' };
      mockUseAuthStore.mockImplementation((selector) => {
        const state = { 
          isAuthenticated: true, 
          user: mockUser, 
          actions: { logout: jest.fn() } 
        };
        return selector(state);
      });

      renderWithProviders(<UserLoginStatus />);
      
      const userButton = screen.getByRole('button', { name: /user menu for testuser/i });
      expect(userButton).toHaveAttribute('aria-expanded', 'false');
      
      await user.click(userButton);
      
      await waitFor(() => {
        expect(userButton).toHaveAttribute('aria-expanded', 'true');
      });
    });
  });
});