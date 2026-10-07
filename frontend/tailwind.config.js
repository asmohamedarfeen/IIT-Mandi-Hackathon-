/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        cardiac: {
          green: '#10B981',
          amber: '#F59E0B',
          red: '#EF4444',
          dark: '#0F172A',
        }
      }
    },
  },
  plugins: [],
}
