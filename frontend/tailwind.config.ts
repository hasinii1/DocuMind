import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        brand: {
          50: "#eef7ff",
          100: "#d9edff",
          200: "#bce0fd",
          300: "#8eccfc",
          400: "#59aff8",
          500: "#328ef3",
          600: "#1d71e7",
          700: "#175bce",
          800: "#184ba6",
          900: "#194184",
          950: "#102852",
        },
      },
    },
  },
  plugins: [],
};
export default config;
