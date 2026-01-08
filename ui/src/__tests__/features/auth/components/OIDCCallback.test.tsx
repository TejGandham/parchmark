import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import OIDCCallback from '../../../../features/auth/components/OIDCCallback';
import { useAuthStore } from '../../../../features/auth/store';

vi.mock('../../../../features/auth/store');
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ state: null }),
  };
});

describe('OIDCCallback', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state on mount', () => {
    const mockActions = {
      handleOIDCCallbackFlow: vi.fn().mockResolvedValue(true),
    };

    vi.mocked(useAuthStore).mockReturnValue({
      actions: mockActions,
    } as any);

    render(
      <MemoryRouter>
        <OIDCCallback />
      </MemoryRouter>
    );

    expect(screen.getByText('Completing authentication...')).toBeInTheDocument();
    expect(screen.getByText('You will be redirected shortly')).toBeInTheDocument();
  });

  it('calls handleOIDCCallbackFlow on mount', async () => {
    const mockNavigate = vi.fn();
    const mockActions = {
      handleOIDCCallbackFlow: vi.fn().mockResolvedValue(true),
    };

    vi.mocked(useAuthStore).mockReturnValue({
      actions: mockActions,
    } as any);

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
      handleOIDCCallbackFlow: vi.fn().mockImplementation(() => new Promise(() => {})),
    };

    vi.mocked(useAuthStore).mockReturnValue({
      actions: mockActions,
    } as any);

    const { container } = render(
      <MemoryRouter>
        <OIDCCallback />
      </MemoryRouter>
    );

    const spinner = container.querySelector('[role="status"]');
    expect(spinner).toBeInTheDocument();
  });
});
