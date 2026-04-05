/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#f1f5f9',
          800: '#ffffff',
          700: '#e2e8f0',
          600: '#cbd5e1'
        }
      }
    },
  },
  plugins: [],
}
