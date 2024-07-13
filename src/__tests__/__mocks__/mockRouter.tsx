import React from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

interface RouterProviderProps {
  children: React.ReactNode;
  initialEntries?: string[];
  initialIndex?: number;
}

export const MockRouterProvider: React.FC<RouterProviderProps> = ({
  children,
  initialEntries = ['/'],
  initialIndex = 0,
}) => {
  return (
    <MemoryRouter initialEntries={initialEntries} initialIndex={initialIndex}>
      {children}
    </MemoryRouter>
  );
};

export const renderWithRouter = (
  ui: React.ReactElement,
  initialEntries: string[] = ['/'],
  initialIndex: number = 0
) => {
  return (
    <MemoryRouter initialEntries={initialEntries} initialIndex={initialIndex}>
      <Routes>
        <Route path="*" element={ui} />
      </Routes>
    </MemoryRouter>
  );
};