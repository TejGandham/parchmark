import { vi, MockedFunction } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ChakraProvider } from '@chakra-ui/react';
import Header from '../../../../features/ui/components/Header';
import { useAuthStore } from '../../../../features/auth/store';

// Mock the auth store
vi.mock('../../../../features/auth/store', () => ({
  useAuthStore: vi.fn(),
}));

const mockUseAuthStore = useAuthStore as MockedFunction<typeof useAuthStore>;

// Mock useBreakpointValue hook for UserInfo component
const mockUseBreakpointValue = vi.fn();
vi.mock('@chakra-ui/react', async () => {
  const actual = await import('@chakra-ui/react');
  return {
    ...actual,
    useBreakpointValue: (...args: unknown[]) => mockUseBreakpointValue(...args),
  };
});

const renderWithProviders = (component: React.ReactNode) => {
  return render(
    <ChakraProvider>
      <BrowserRouter>{component}</BrowserRouter>
    </ChakraProvider>
  );
};

describe('Header Component', () => {
  const toggleSidebar = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBreakpointValue.mockReturnValue(true); // Default to desktop view
    mockUseAuthStore.mockReturnValue(false); // Default to not authenticated
  });

  it('should render the app title', () => {
    renderWithProviders(<Header toggleSidebar={toggleSidebar} />);

    expect(screen.getByAltText(/ParchMark Logo/i)).toBeInTheDocument();
  });

  it('should call toggleSidebar when menu button is clicked', () => {
    renderWithProviders(<Header toggleSidebar={toggleSidebar} />);

    // Find the toggle sidebar button (there should be multiple buttons now due to UserLoginStatus)
    const menuButton = screen.getByLabelText(/toggle sidebar/i);
    fireEvent.click(menuButton);

    expect(toggleSidebar).toHaveBeenCalledTimes(1);
  });

  it('should render as a header element with correct structure', () => {
    renderWithProviders(<Header toggleSidebar={toggleSidebar} />);

    const header = screen.getByRole('banner');
    expect(header).toBeInTheDocument();

    // Verify the header has the expected structure
    expect(header.tagName).toBe('HEADER');

    // Check that both the menu button and user status are present
    expect(screen.getByLabelText(/toggle sidebar/i)).toBeInTheDocument();
    expect(
      screen.getByRole('region', { name: 'User authentication status' })
    ).toBeInTheDocument();
  });

  it('should be accessible', () => {
    renderWithProviders(<Header toggleSidebar={toggleSidebar} />);

    // Check if the toggle sidebar button has accessible attributes
    const menuButton = screen.getByLabelText(/toggle sidebar/i);
    expect(menuButton).toHaveAttribute('aria-label');
  });

  it('should render UserLoginStatus component', () => {
    renderWithProviders(<Header toggleSidebar={toggleSidebar} />);

    // Should render the sign in button when not authenticated
    const signInButton = screen.getByRole('button', {
      name: /sign in to your account/i,
    });
    expect(signInButton).toBeInTheDocument();
  });

  it('should render user info when authenticated', () => {
    // Mock authenticated user
    const mockUser = { username: 'testuser', password: '' };
    mockUseAuthStore.mockImplementation((selector) => {
      const state = {
        isAuthenticated: true,
        user: mockUser,
        actions: { logout: vi.fn() },
      };
      return selector(state);
    });

    renderWithProviders(<Header toggleSidebar={toggleSidebar} />);

    // Should render user button when authenticated
    const userButton = screen.getByRole('button', {
      name: /user menu for testuser/i,
    });
    expect(userButton).toBeInTheDocument();
  });

});
