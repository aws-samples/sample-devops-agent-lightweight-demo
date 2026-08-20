import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Production build only — the app is served via CloudFront, not a local dev server.
export default defineConfig({
  plugins: [react()],
})
