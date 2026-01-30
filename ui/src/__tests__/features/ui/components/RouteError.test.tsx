// ui/src/__tests__/features/ui/components/RouteError.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChakraProvider } from '@chakra-ui/react';
import { MemoryRouter } from 'react-router-dom';
import * as routerDom from 'react-router-dom';

// Mock the useRouteError hook and isRouteErrorResponse
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useRouteError: vi.fn(),
    isRouteErrorResponse: vi.fn(),
  };
});

describe('RouteError', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders 401 error with login link', async () => {
    const error = { status: 401, statusText: 'Unauthorized', data: null };
    vi.mocked(routerDom.useRouteError).mockReturnValue(error);
    vi.mocked(routerDom.isRouteErrorResponse).mockReturnValue(true);

    const { default: RouteError } = await import(
      '../../../../features/ui/components/RouteError'
    );

    render(
      <ChakraProvider>
        <MemoryRouter>
          <RouteError />
        </MemoryRouter>
      </ChakraProvider>
    );

    expect(screen.getByText('Session Expired')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /log in/i })).toHaveAttribute(
      'href',
      '/login'
    );
  });

  it('renders generic HTTP error', async () => {
    const error = { status: 404, statusText: 'Not Found', data: null };
    vi.mocked(routerDom.useRouteError).mockReturnValue(error);
    vi.mocked(routerDom.isRouteErrorResponse).mockReturnValue(true);

    const { default: RouteError } = await import(
      '../../../../features/ui/components/RouteError'
    );

    render(
      <ChakraProvider>
        <MemoryRouter>
          <RouteError />
        </MemoryRouter>
      </ChakraProvider>
    );

    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText('Not Found')).toBeInTheDocument();
  });

  it('renders thrown Error', async () => {
    const error = new Error('Something broke');
    vi.mocked(routerDom.useRouteError).mockReturnValue(error);
    vi.mocked(routerDom.isRouteErrorResponse).mockReturnValue(false);

    const { default: RouteError } = await import(
      '../../../../features/ui/components/RouteError'
    );

    render(
      <ChakraProvider>
        <MemoryRouter>
          <RouteError />
        </MemoryRouter>
      </ChakraProvider>
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Something broke')).toBeInTheDocument();
  });
});
