import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import theme from '../../styles/theme';
import { renderWithRouter } from './mockRouter';

interface TestProviderProps {
  children: React.ReactNode;
}

// Provider wrapper with Chakra UI theme
export const TestProvider: React.FC<TestProviderProps> = ({ children }) => {
  return <ChakraProvider theme={theme}>{children}</ChakraProvider>;
};

// Custom render with providers
export const renderWithProviders = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, { wrapper: TestProvider, ...options });
};

// Render with both Router and ChakraProvider
export const renderWithRouterAndProviders = (
  ui: React.ReactElement,
  initialEntries: string[] = ['/'],
  initialIndex: number = 0
) => {
  const wrapped = renderWithRouter(ui, initialEntries, initialIndex);
  return renderWithProviders(wrapped);
};

// Mock responsive breakpoints for testing
export const mockBreakpoint = (
  breakpoint: 'base' | 'sm' | 'md' | 'lg' | 'xl'
) => {
  // Chakra UI default breakpoints: sm: '30em', md: '48em', lg: '62em', xl: '80em'
  const matchMediaQueries: Record<string, boolean> = {
    '(min-width: 30em)': ['sm', 'md', 'lg', 'xl'].includes(breakpoint), // sm and up (480px)
    '(min-width: 48em)': ['md', 'lg', 'xl'].includes(breakpoint), // md and up (768px)
    '(min-width: 62em)': ['lg', 'xl'].includes(breakpoint), // lg and up (992px)
    '(min-width: 80em)': breakpoint === 'xl', // xl and up (1280px)
  };

  (window.matchMedia as jest.Mock).mockImplementation((query: string) => ({
    matches: matchMediaQueries[query] || false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
};

// Mock Chakra UI's useBreakpointValue hook directly
export const mockUseBreakpointValue = (
  values: Record<string, string | number | boolean>,
  currentBreakpoint: string
) => {
  const chakraUI = jest.requireActual('@chakra-ui/react');
  return {
    ...chakraUI,
    useBreakpointValue: jest.fn().mockImplementation((responsiveValues) => {
      if (typeof responsiveValues === 'object' && responsiveValues !== null) {
        // Find the appropriate value for the current breakpoint
        if (currentBreakpoint === 'base') return responsiveValues.base;
        if (currentBreakpoint === 'sm')
          return responsiveValues.sm || responsiveValues.base;
        if (currentBreakpoint === 'md')
          return (
            responsiveValues.md || responsiveValues.sm || responsiveValues.base
          );
        if (currentBreakpoint === 'lg')
          return (
            responsiveValues.lg ||
            responsiveValues.md ||
            responsiveValues.sm ||
            responsiveValues.base
          );
        if (currentBreakpoint === 'xl')
          return (
            responsiveValues.xl ||
            responsiveValues.lg ||
            responsiveValues.md ||
            responsiveValues.sm ||
            responsiveValues.base
          );
        return responsiveValues.base;
      }
      return responsiveValues;
    }),
  };
};
