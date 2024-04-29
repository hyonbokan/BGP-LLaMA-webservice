/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx}",
    "./public/index.html",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        'roboto-mono': ['Roboto Mono', 'monospace'],
        'roboto-condensed': ['Roboto Condensed', 'sans-serif']
      }
    },
  },
  plugins: [],
}