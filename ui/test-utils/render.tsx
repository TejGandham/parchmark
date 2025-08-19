import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter } from 'react-router-dom';
import theme from '../src/styles/theme';

interface TestProviderProps {
  children: React.ReactNode;
}

// All the providers that wrap our app
const AllTheProviders: React.FC<TestProviderProps> = ({ children }) => {
  return (
    <ChakraProvider theme={theme}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </ChakraProvider>
  );
};

// Custom render function that includes providers
const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';

// Override render method
export { customRender as render };
