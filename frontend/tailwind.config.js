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
      },
    },
  },
  plugins: [],
}
