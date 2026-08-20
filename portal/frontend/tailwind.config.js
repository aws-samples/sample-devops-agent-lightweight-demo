/** @type {import('tailwindcss').Config} */
export default {
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
