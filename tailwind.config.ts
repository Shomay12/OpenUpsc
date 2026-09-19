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
        background: "#FAFAF8",
        surface: "#FFFFFF",
        surfaceHover: "#F6F6F4",
        foreground: "#0F172A",
        muted: "#64748B",
        mutedLight: "#94A3B8",
        borderSubtle: "rgba(15, 23, 42, 0.07)",
        borderHover: "rgba(15, 23, 42, 0.15)",
        brand: {
          50: "#F0F4FF",
          100: "#E0EBFF",
          500: "#3B82F6",
          600: "#2563EB",
          900: "#0F172A",
          950: "#0A0F1D",
        },
        accent: {
          DEFAULT: "#0F172A",
          blue: "#2563EB",
          subtle: "#F1F5F9",
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        display: ["var(--font-display)", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '24px',
        '4xl': '32px',
      },
      boxShadow: {
        subtle: "0 1px 2px 0 rgba(0, 0, 0, 0.03)",
        card: "0 2px 8px -2px rgba(15, 23, 42, 0.04), 0 1px 4px -1px rgba(15, 23, 42, 0.02)",
        cardHover: "0 12px 32px -8px rgba(15, 23, 42, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.03)",
        floating: "0 16px 40px -12px rgba(15, 23, 42, 0.12), 0 0 0 1px rgba(15, 23, 42, 0.06)",
        command: "0 24px 60px -15px rgba(15, 23, 42, 0.2), 0 0 0 1px rgba(15, 23, 42, 0.08)",
      },
      letterSpacing: {
        tighter: '-0.04em',
        tight: '-0.02em',
      }
    },
  },
  plugins: [],
};
export default config;
