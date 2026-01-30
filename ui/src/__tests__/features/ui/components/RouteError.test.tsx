// ui/src/__tests__/features/ui/components/RouteError.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';

// We'll test RouteError by triggering actual route errors
describe('RouteError', () => {
  it('renders 401 error with login link', async () => {
    const { default: RouteError } = await import(
      '../../../../features/ui/components/RouteError'
    );

    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <div>Home</div>,
          errorElement: <RouteError />,
          loader: () => {
            throw new Response('Unauthorized', { status: 401 });
          },
        },
      ],
      { initialEntries: ['/'] }
    );

    render(<RouterProvider router={router} />);

    expect(await screen.findByText('Session Expired')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /log in/i })).toHaveAttribute(
      'href',
      '/login'
    );
  });

  it('renders generic HTTP error', async () => {
    const { default: RouteError } = await import(
      '../../../../features/ui/components/RouteError'
    );

    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <div>Home</div>,
          errorElement: <RouteError />,
          loader: () => {
            throw new Response('Not Found', { status: 404, statusText: 'Not Found' });
          },
        },
      ],
      { initialEntries: ['/'] }
    );

    render(<RouterProvider router={router} />);

    expect(await screen.findByText('404')).toBeInTheDocument();
    expect(screen.getByText('Not Found')).toBeInTheDocument();
  });

  it('renders thrown Error', async () => {
    const { default: RouteError } = await import(
      '../../../../features/ui/components/RouteError'
    );

    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <div>Home</div>,
          errorElement: <RouteError />,
          loader: () => {
            throw new Error('Something broke');
          },
        },
      ],
      { initialEntries: ['/'] }
    );

    render(<RouterProvider router={router} />);

    expect(await screen.findByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Something broke')).toBeInTheDocument();
  });
});
