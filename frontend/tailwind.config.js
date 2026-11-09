/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#102A56',
          blue: '#0f8f91',
          cyan: '#32b8b2',
          green: '#138a72',
          amber: '#f59e0b',
          red: '#ef4444',
        },
        surface: '#F5F7FB',
      },
      boxShadow: {
        card: '0 1px 2px rgba(15, 23, 42, 0.03), 0 8px 24px rgba(15, 23, 42, 0.04)',
      },
    },
  },
  plugins: [],
};
