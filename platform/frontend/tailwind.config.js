/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
        surface: {
          50: "#f0f0f5",
          100: "#d4d4dd",
          200: "#9ca3af",
          300: "#6b7280",
          400: "#4b5563",
          500: "#374151",
          600: "#1e1e30",
          700: "#13131f",
          800: "#0c0c14",
          900: "#06060b",
        },
        accent: {
          green: "#34d399",
          red: "#f87171",
          yellow: "#fbbf24",
          purple: "#a78bfa",
          cyan: "#22d3ee",
          orange: "#fb923c",
          pink: "#f472b6",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease forwards",
        "slide-up": "slideUp 0.6s cubic-bezier(0.16,1,0.3,1) forwards",
        "pulse-glow": "pulse-glow 3s ease-in-out infinite",
        shimmer: "shimmer 3s linear infinite",
      },
    },
  },
  plugins: [],
};
