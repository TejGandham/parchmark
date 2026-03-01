import { vi, MockedFunction } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ChakraProvider } from '@chakra-ui/react';
import Header from '../../../../features/ui/components/Header';
import { useAuthStore } from '../../../../features/auth/store';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../../../../features/auth/store', () => ({
  useAuthStore: vi.fn(),
}));

const mockOpenPalette = vi.fn();

vi.mock('../../../../features/ui/store/ui', () => ({
  useUIStore: vi.fn((selector) => {
    const state = {
      actions: { openPalette: mockOpenPalette },
    };
    return selector ? selector(state) : state;
  }),
}));

const mockUseAuthStore = useAuthStore as MockedFunction<typeof useAuthStore>;

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
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseBreakpointValue.mockReturnValue(true);
    mockUseAuthStore.mockReturnValue(false);
    mockNavigate.mockClear();
  });

  it('should render the app logo', () => {
    renderWithProviders(<Header />);
    expect(screen.getByAltText(/ParchMark Logo/i)).toBeInTheDocument();
  });

  it('should render palette trigger button', () => {
    renderWithProviders(<Header />);
    const trigger = screen.getByTestId('palette-trigger');
    expect(trigger).toBeInTheDocument();
    expect(trigger).toHaveTextContent(/Search notes…/);
  });

  it('should call openPalette when palette trigger is clicked', () => {
    renderWithProviders(<Header />);
    const trigger = screen.getByTestId('palette-trigger');
    fireEvent.click(trigger);
    expect(mockOpenPalette).toHaveBeenCalledTimes(1);
  });

  it('should render as a header element with correct structure', () => {
    renderWithProviders(<Header />);

    const header = screen.getByRole('banner');
    expect(header).toBeInTheDocument();
    expect(header.tagName).toBe('HEADER');
    expect(
      screen.getByRole('region', { name: 'User authentication status' })
    ).toBeInTheDocument();
  });

  it('should not have a sidebar toggle button', () => {
    renderWithProviders(<Header />);
    expect(screen.queryByLabelText(/toggle sidebar/i)).not.toBeInTheDocument();
  });

  it('should render UserLoginStatus component', () => {
    renderWithProviders(<Header />);
    const signInButton = screen.getByRole('button', {
      name: /sign in to your account/i,
    });
    expect(signInButton).toBeInTheDocument();
  });

  it('should render user info when authenticated', () => {
    const mockUser = { username: 'testuser', password: '' };
    mockUseAuthStore.mockImplementation((selector) => {
      const state = {
        isAuthenticated: true,
        user: mockUser,
        actions: { logout: vi.fn() },
      };
      return selector(state);
    });

    renderWithProviders(<Header />);

    const userButton = screen.getByRole('button', {
      name: /user menu for testuser/i,
    });
    expect(userButton).toBeInTheDocument();
  });

  it('should render explorer link button', () => {
    renderWithProviders(<Header />);
    const explorerLink = screen.getByTestId('explorer-link');
    expect(explorerLink).toBeInTheDocument();
  });

  it('should navigate to /notes/explore when explorer button is clicked', () => {
    renderWithProviders(<Header />);
    const explorerLink = screen.getByTestId('explorer-link');
    fireEvent.click(explorerLink);
    expect(mockNavigate).toHaveBeenCalledWith('/notes/explore');
  });
});
