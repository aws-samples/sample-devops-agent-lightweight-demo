/** @type {import('tailwindcss').Config} */
// NOTE: This file must stay CommonJS (.cjs). package.json sets "type": "module",
// so a .js config would be treated as ESM, which tailwindcss@3.3.0 cannot load —
// it silently falls back to an empty config, emitting preflight but no utilities.
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        success: '#10b981',
        error: '#ef4444',
        neutral: '#6b7280',
        accent: '#3b82f6',
      }
    },
  },
  plugins: [],
}
