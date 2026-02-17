import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/base/global.css';
import App from './App.tsx';
import { getVersionString, getVersionInfo } from './version';

if (typeof window !== 'undefined') {
  (window as Record<string, unknown>).__PARCHMARK__ = getVersionInfo();
  console.info(`ParchMark ${getVersionString()}`);
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
