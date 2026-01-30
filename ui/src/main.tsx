import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/base/global.css';
import App from './App.tsx';

// Create the React root and render the app
// Note: App uses RouterProvider which handles routing internally
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
