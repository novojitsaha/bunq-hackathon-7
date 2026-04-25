import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#16201d",
        mint: "#54b689",
        coral: "#ef7667",
        amber: "#e9aa3f",
        berry: "#8f5c7e",
        cloud: "#f6f7f4",
      },
      boxShadow: {
        panel: "0 16px 48px rgba(35, 48, 42, 0.08)",
      },
    },
  },
  plugins: [],
} satisfies Config;

