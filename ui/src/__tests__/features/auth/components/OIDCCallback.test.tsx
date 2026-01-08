import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import OIDCCallback from '../../../../features/auth/components/OIDCCallback';
import { useAuthStore, AuthState } from '../../../../features/auth/store';

vi.mock('../../../../features/auth/store');
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ state: null }),
  };
});

// Helper to create a partial mock of AuthState
const createMockAuthState = (
  overrides: Partial<AuthState>
): Partial<AuthState> => ({
  isAuthenticated: false,
  user: null,
  token: null,
  refreshToken: null,
  tokenSource: 'local',
  error: null,
  oidcLogoutWarning: null,
  _refreshPromise: null,
  ...overrides,
});

describe('OIDCCallback', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state on mount', () => {
    const mockActions = {
      handleOIDCCallbackFlow: vi.fn().mockResolvedValue(true),
    } as Pick<AuthState['actions'], 'handleOIDCCallbackFlow'>;

    vi.mocked(useAuthStore).mockReturnValue(
      createMockAuthState({ actions: mockActions as AuthState['actions'] })
    );

    render(
      <MemoryRouter>
        <OIDCCallback />
      </MemoryRouter>
    );

    expect(
      screen.getByText('Completing authentication...')
    ).toBeInTheDocument();
    expect(
      screen.getByText('You will be redirected shortly')
    ).toBeInTheDocument();
  });

  it('calls handleOIDCCallbackFlow on mount', async () => {
    const mockNavigate = vi.fn();
    const mockActions = {
      handleOIDCCallbackFlow: vi.fn().mockResolvedValue(true),
    } as Pick<AuthState['actions'], 'handleOIDCCallbackFlow'>;

    vi.mocked(useAuthStore).mockReturnValue(
      createMockAuthState({ actions: mockActions as AuthState['actions'] })
    );

    vi.stubGlobal('useNavigate', () => mockNavigate);

    render(
      <MemoryRouter>
        <OIDCCallback />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(mockActions.handleOIDCCallbackFlow).toHaveBeenCalled();
    });
  });

  it('shows spinner while processing', () => {
    const mockActions = {
      handleOIDCCallbackFlow: vi
        .fn()
        .mockImplementation(() => new Promise(() => {})),
    } as Pick<AuthState['actions'], 'handleOIDCCallbackFlow'>;

    vi.mocked(useAuthStore).mockReturnValue(
      createMockAuthState({ actions: mockActions as AuthState['actions'] })
    );

    const { container } = render(
      <MemoryRouter>
        <OIDCCallback />
      </MemoryRouter>
    );

    // Look for the spinner element - Chakra UI Spinner uses a div with specific class
    const spinner = container.querySelector('.chakra-spinner');
    expect(spinner).toBeInTheDocument();
  });
});
