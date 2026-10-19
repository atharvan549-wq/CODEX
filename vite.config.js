import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// GitHub Pages hosts this repository under /CODEX/.
// Netlify serves the site from the domain root, so use '/' there.
const base = process.env.NETLIFY === 'true' ? '/' : '/CODEX/';

export default defineConfig({
  plugins: [react()],
  base,
});
