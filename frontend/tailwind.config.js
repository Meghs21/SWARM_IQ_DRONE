/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0e17',
        surface: '#111827',
        'surface-card': '#1a2234',
        accent: '#06b6d4',
        'accent-hover': '#0891b2',
        danger: '#ef4444',
        warning: '#f59e0b',
        success: '#10b981',
      }
    },
  },
  plugins: [],
}
