import { vi } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { TestProvider } from '../../../__mocks__/testUtils';
import NotFoundPage from '../../../../features/ui/components/NotFoundPage';

// Mock react-router-dom
vi.mock('react-router-dom', async () => ({
  ...(await import('react-router-dom')),
  Link: ({ to, children }) => (
    <a href={to} data-testid={`link-to-${to}`}>
      {children}
    </a>
  ),
}));

describe('NotFoundPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <TestProvider>
          <NotFoundPage />
        </TestProvider>
      </MemoryRouter>
    );
  };

  it('should render the 404 message', () => {
    renderComponent();

    expect(screen.getByText(/404/i)).toBeInTheDocument();
    expect(
      screen.getByText(/note not found/i, { exact: false })
    ).toBeInTheDocument();
  });

  it('should have a button to go back to notes page', () => {
    renderComponent();

    const backButton = screen.getByRole('button', { name: /back to notes/i });
    expect(backButton).toBeInTheDocument();
  });

  it('should have a link to the notes page', () => {
    renderComponent();

    const backLink = screen.getByTestId('link-to-/notes');
    expect(backLink).toBeInTheDocument();
    expect(backLink).toHaveAttribute('href', '/notes');
  });

  it('should have appropriate styling for error page', () => {
    renderComponent();

    // The 404 should be prominently displayed
    const title = screen.getByText(/404/i);
    expect(title).toBeInTheDocument();

    // Check that there are appropriate headings
    const headings = screen.getAllByRole('heading');
    expect(headings.length).toBeGreaterThanOrEqual(2);

    // Check for the description text
    expect(
      screen.getByText(/doesn't exist or may have been deleted/i)
    ).toBeInTheDocument();
  });
});
