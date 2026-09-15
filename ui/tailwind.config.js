/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          0: "#0f0f0f",
          1: "#1a1a1a",
          2: "#252525",
          3: "#2f2f2f",
        },
        accent: "#7c6fcd",
      },
    },
  },
  plugins: [],
};
