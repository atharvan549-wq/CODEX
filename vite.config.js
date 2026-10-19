import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// GitHub Pages serves this project under /CODEX/.
// For a custom domain or a different hosting provider, change base to '/'.
export default defineConfig({
  plugins: [react()],
  base: '/CODEX/',
});
