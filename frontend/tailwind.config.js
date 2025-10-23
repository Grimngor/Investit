/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  darkMode: 'class', // use .dark class on html root
  theme: {
    extend: {
      // Custom colors (optional fine-tuning for dark mode aesthetics)
      colors: {
        navy: {
          900: '#060d16',
          800: '#0b1726',
        },
        softblue: {
          50: '#f4f8fc',
          100: '#e8f1f9',
          200: '#d4e4f3',
          300: '#b7d3eb',
          400: '#91b8de',
          500: '#6a9ccc',
          600: '#4a7fb1',
          700: '#38618a',
          800: '#294562',
          900: '#1c2f42',
        },
      },
    },
  },
  plugins: [],
}
