// ui/src/__tests__/AppDataRouter.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

vi.mock('../router', () => ({
  router: {
    navigate: vi.fn(),
    state: { location: { pathname: '/login' } },
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    RouterProvider: () => <div data-testid="router-provider">Router Active</div>,
  };
});

vi.mock('../features/auth/hooks/useTokenExpirationMonitor', () => ({
  useTokenExpirationMonitor: vi.fn(),
}));

describe('App with Data Router', () => {
  it('renders with RouterProvider', async () => {
    const { default: App } = await import('../App');
    render(<App />);
    expect(screen.getByTestId('router-provider')).toBeInTheDocument();
  });

  it('calls useTokenExpirationMonitor', async () => {
    const { useTokenExpirationMonitor } = await import(
      '../features/auth/hooks/useTokenExpirationMonitor'
    );
    const { default: App } = await import('../App');
    render(<App />);
    expect(useTokenExpirationMonitor).toHaveBeenCalled();
  });
});
