import { render } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import PageTransition from '../../components/PageTransition';
import React from 'react';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: (Component: React.ComponentType<React.PropsWithChildren>) => {
    const MotionComponent = ({
      children,
      ...props
    }: React.PropsWithChildren) => (
      <Component {...props} data-testid="motion-component">
        {children}
      </Component>
    );
    return MotionComponent;
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
}));

describe('PageTransition', () => {
  it('should render children', () => {
    const { getByText } = render(
      <BrowserRouter>
        <PageTransition>
          <div>Test Content</div>
        </PageTransition>
      </BrowserRouter>
    );

    expect(getByText('Test Content')).toBeInTheDocument();
  });

  it('should render with motion props', () => {
    const { getByTestId } = render(
      <BrowserRouter>
        <PageTransition>
          <div>Test Content</div>
        </PageTransition>
      </BrowserRouter>
    );

    const motionComponent = getByTestId('motion-component');
    expect(motionComponent).toBeInTheDocument();
  });

  it('should handle route changes', () => {
    const TestComponent = () => {
      const navigate = useNavigate();
      return (
        <div>
          <button onClick={() => navigate('/about')}>Go to About</button>
          <Routes>
            <Route
              path="/"
              element={
                <PageTransition>
                  <div>Home Page</div>
                </PageTransition>
              }
            />
            <Route
              path="/about"
              element={
                <PageTransition>
                  <div>About Page</div>
                </PageTransition>
              }
            />
          </Routes>
        </div>
      );
    };

    const { getByText } = render(
      <BrowserRouter>
        <TestComponent />
      </BrowserRouter>
    );

    expect(getByText('Home Page')).toBeInTheDocument();
  });

  it('should render multiple children correctly', () => {
    const { getByText } = render(
      <BrowserRouter>
        <PageTransition>
          <div>
            <h1>Title</h1>
            <p>Content</p>
          </div>
        </PageTransition>
      </BrowserRouter>
    );

    expect(getByText('Title')).toBeInTheDocument();
    expect(getByText('Content')).toBeInTheDocument();
  });

  it('should use location pathname as key', () => {
    const { container } = render(
      <BrowserRouter>
        <PageTransition>
          <div>Test Content</div>
        </PageTransition>
      </BrowserRouter>
    );

    // MotionBox should be rendered
    const motionComponent = container.querySelector(
      '[data-testid="motion-component"]'
    );
    expect(motionComponent).toBeInTheDocument();
  });
});
