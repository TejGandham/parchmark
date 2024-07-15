import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TestProvider } from '../../../__mocks__/testUtils';
import Header from '../../../../features/ui/components/Header';

describe('Header Component', () => {
  const toggleSidebar = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render the app title', () => {
    render(
      <TestProvider>
        <Header toggleSidebar={toggleSidebar} />
      </TestProvider>
    );

    expect(screen.getByText(/parchmark/i)).toBeInTheDocument();
  });

  it('should call toggleSidebar when menu button is clicked', () => {
    render(
      <TestProvider>
        <Header toggleSidebar={toggleSidebar} />
      </TestProvider>
    );

    // Find the button (might be a button with an icon)
    const menuButton = screen.getByRole('button');
    fireEvent.click(menuButton);

    expect(toggleSidebar).toHaveBeenCalledTimes(1);
  });

  it('should have the correct styling', () => {
    render(
      <TestProvider>
        <Header toggleSidebar={toggleSidebar} />
      </TestProvider>
    );

    const header = screen.getByRole('banner');
    expect(header).toBeInTheDocument();

    // Check for specific styling based on the actual component implementation
    expect(header).toHaveStyle('box-shadow: var(--chakra-shadows-sm)');
    expect(header).toHaveStyle('border-bottom: 1px solid #e2e8f0');
  });

  it('should be accessible', () => {
    render(
      <TestProvider>
        <Header toggleSidebar={toggleSidebar} />
      </TestProvider>
    );

    // Check if the button has accessible attributes
    const menuButton = screen.getByRole('button');
    expect(menuButton).toHaveAttribute('aria-label');
  });
});
