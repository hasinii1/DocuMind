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
          50: "#fff0f7",
          100: "#fce0ed",
          200: "#f6bdd7",
          300: "#ed8fbb",
          400: "#dd5995",
          500: "#b92d73",
          600: "#890149",
          700: "#70003c",
          800: "#56002e",
          900: "#410022",
          950: "#2d0018",
        },
      },
    },
  },
  plugins: [],
};
export default config;
