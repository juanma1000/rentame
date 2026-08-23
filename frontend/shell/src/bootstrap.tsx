import React from 'react';
import { createRoot } from 'react-dom/client';
import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/700.css';
import '@fontsource/dm-serif-display';
import '@rentame/design-tokens/src/tokens.css';
import App from './App';

const container = document.getElementById('root');
if (!container) {
  throw new Error('[rentame-shell] Root element #root not found in DOM.');
}

createRoot(container).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
