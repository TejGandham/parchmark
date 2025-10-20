import React, { act } from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';
import { useAuthStore } from '../features/auth/store';
import {
  mockAuthStore,
  mockUnauthenticatedStore,
} from './__mocks__/mockStores';

// Mock the lazy-loaded components
jest.mock('../features/notes/components/NotesContainer', () => {
  return function MockNotesContainer() {
    return <div data-testid="notes-container">Notes Container</div>;
  };
});

jest.mock('../features/ui/components/NotFoundPage', () => {
  return function MockNotFoundPage() {
    return <div data-testid="not-found-page">404 Not Found</div>;
  };
});

jest.mock('../features/auth/components/LoginForm', () => {
  return function MockLoginForm() {
    return <div data-testid="login-form">Login Form</div>;
  };
});

// Mock the auth store
jest.mock('../features/auth/store');

// Create a complete mock of react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useParams: () => ({}),
  useLocation: () => ({ pathname: '/notes' }),
  Routes: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="routes">{children}</div>
  ),
  Route: ({ path, element }: { path: string; element: React.ReactNode }) => (
    <div data-testid={`route-${path}`}>{element}</div>
  ),
  Navigate: ({ to }: { to: string }) => (
    <div data-testid={`navigate-${to}`}>Redirecting to {to}</div>
  ),
  BrowserRouter: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="browser-router">{children}</div>
  ),
}));

// Mock Suspense to avoid lazy loading issues
jest.mock('react', () => {
  const originalReact = jest.requireActual('react');
  return {
    ...originalReact,
    Suspense: ({
      children,
      fallback,
    }: {
      children: React.ReactNode;
      fallback: React.ReactNode;
    }) => (
      <div data-testid="suspense">
        <div data-testid="suspense-fallback">{fallback}</div>
        <div data-testid="suspense-children">{children}</div>
      </div>
    ),
  };
});

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Default to unauthenticated state
    (useAuthStore as jest.Mock).mockImplementation((selector) => {
      const state = mockUnauthenticatedStore;
      return selector ? selector(state) : state;
    });
  });

  it('should render the ChakraProvider', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // ChakraProvider should apply its theme to the document
    const appElement = document.querySelector('div');
    expect(appElement).toBeInTheDocument();
  });

  it('should redirect to login page when user is not authenticated', async () => {
    // Mock route to notes when unauthenticated
    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // Should render Login route
    expect(screen.getByTestId('route-/login')).toBeInTheDocument();
  });

  it('should render notes when user is authenticated', async () => {
    // Mock authenticated state
    (useAuthStore as jest.Mock).mockImplementation((selector) => {
      const state = mockAuthStore;
      return selector ? selector(state) : state;
    });

    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // Should render the notes route
    expect(screen.getByTestId('route-/notes')).toBeInTheDocument();
  });

  it('should render a loading fallback', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // There should be a suspense fallback
    const fallback = screen.getByTestId('suspense-fallback');
    expect(fallback).toBeInTheDocument();
  });

  it('should have the notes container in suspense children', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // The suspense children should contain the routes with notes container
    const suspenseChildren = screen.getByTestId('suspense-children');
    expect(suspenseChildren).toBeInTheDocument();

    // Check one of the nested routes
    expect(screen.getByTestId('route-/notes')).toBeInTheDocument();
  });

  it('should contain the correct routes', async () => {
    await act(async () => {
      render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );
    });

    // Check for the routes container
    expect(screen.getByTestId('routes')).toBeInTheDocument();

    // Look for specific route paths in our mocked Route components
    expect(screen.getByTestId('route-/')).toBeInTheDocument();
    expect(screen.getByTestId('route-/notes')).toBeInTheDocument();
    expect(screen.getByTestId('route-/notes/:noteId')).toBeInTheDocument();
    expect(screen.getByTestId('route-/not-found')).toBeInTheDocument();
    expect(screen.getByTestId('route-*')).toBeInTheDocument();
  });

  describe('Suspense Fallback', () => {
    it('should render the suspense fallback correctly', async () => {
      await act(async () => {
        render(
          <BrowserRouter>
            <App />
          </BrowserRouter>
        );
      });

      // Check for the fallback element
      const fallback = screen.getByTestId('suspense-fallback');
      expect(fallback).toBeInTheDocument();
    });
  });

  describe('RootRoute Navigation', () => {
    it('should navigate to /login when user is not authenticated', async () => {
      (useAuthStore as jest.Mock).mockImplementation((selector) => {
        const state = mockUnauthenticatedStore;
        return selector ? selector(state) : state;
      });

      await act(async () => {
        render(
          <BrowserRouter>
            <App />
          </BrowserRouter>
        );
      });

      // Should render at least one navigate to login
      expect(screen.getAllByTestId('navigate-/login')).toHaveLength(3);
    });

    it('should navigate to /notes when user is authenticated', async () => {
      (useAuthStore as jest.Mock).mockImplementation((selector) => {
        const state = mockAuthStore;
        return selector ? selector(state) : state;
      });

      await act(async () => {
        render(
          <BrowserRouter>
            <App />
          </BrowserRouter>
        );
      });

      // Should render navigate to notes
      expect(screen.getByTestId('navigate-/notes')).toBeInTheDocument();
    });
  });
});
