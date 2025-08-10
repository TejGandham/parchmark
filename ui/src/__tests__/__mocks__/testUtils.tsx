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
