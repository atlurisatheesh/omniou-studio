import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        agri: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
          900: "#14532d",
        },
        soil: {
          50: "#faf5f0",
          100: "#f0e6d3",
          200: "#e0cca7",
          300: "#cba66f",
          400: "#b8864a",
          500: "#a87035",
          600: "#8a5828",
          700: "#6e4422",
          800: "#5c3921",
          900: "#4e311e",
        },
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};

export default config;
