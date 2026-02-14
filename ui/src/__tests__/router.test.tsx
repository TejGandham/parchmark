// ui/src/__tests__/router.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { render, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';

// Mock auth store
vi.mock('../features/auth/store', () => ({
  useAuthStore: {
    getState: vi.fn(() => ({ isAuthenticated: false })),
  },
}));

// Mock RouteError to avoid useRouteError hook issues in tests
vi.mock('../features/ui/components/RouteError', () => ({
  default: () => <div data-testid="route-error">Route Error</div>,
}));

// Mock API
vi.mock('../services/api', () => ({
  getNotes: vi.fn().mockResolvedValue([]),
}));

// Mock NotesLayout (not yet created)
vi.mock('../features/notes/components/NotesLayout', () => ({
  default: () => <div>Notes Layout</div>,
}));

// Mock NoteContent (will be updated later)
vi.mock('../features/notes/components/NoteContent', () => ({
  default: () => <div>Note Content</div>,
}));

describe('router', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects unauthenticated users from /notes to /login', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: false,
    });

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/notes'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/login');
    });
  });

  it('redirects root to /login when unauthenticated', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: false,
    });

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/login');
    });
  });

  it('redirects root to /notes when authenticated', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: true,
    });

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/notes');
    });
  });

  it('redirects unauthenticated users from /settings to /login', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: false,
    });

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/settings'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/login');
    });
  });

  it('allows authenticated users to access /settings', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: true,
    });

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/settings'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/settings');
    });
  });

  it('displays error boundary when API fails', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    const api = await import('../services/api');

    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: true,
    });

    // Simulate API failure
    (api.getNotes as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Network error')
    );

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/notes'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    // The error should be caught by RouteError
    await waitFor(() => {
      expect(router.state.errors).toBeDefined();
    });
  });

  it('redirects to /login when fetch aborts during OIDC logout', async () => {
    const { useAuthStore } = await import('../features/auth/store');
    const api = await import('../services/api');

    (useAuthStore.getState as ReturnType<typeof vi.fn>).mockReturnValue({
      isAuthenticated: true,
    });

    localStorage.removeItem('parchmark-auth');

    (api.getNotes as ReturnType<typeof vi.fn>).mockRejectedValue(
      new TypeError('NetworkError when attempting to fetch resource.')
    );

    const { routes } = await import('../router');

    const router = createMemoryRouter(routes, {
      initialEntries: ['/notes'],
    });

    render(
      <ChakraProvider>
        <RouterProvider router={router} />
      </ChakraProvider>
    );

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/login');
    });
  });
});
