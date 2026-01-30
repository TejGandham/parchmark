// ui/src/__tests__/router.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';

// Mock auth store
vi.mock('../features/auth/store', () => ({
  useAuthStore: {
    getState: vi.fn(() => ({ isAuthenticated: false })),
  },
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
});
