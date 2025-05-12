/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Libre Franklin"', "sans-serif"],
      },
      colors: {
        background: {
          light: "#ffffff",
          dark: "#121212",
        },
        surface: {
          light: "#f5f6fa",
          dark: "#1e1e1e",
        },
        primary: {
          light: "#0052cc",
          dark: "#3399ff",
        },
        secondary: {
          light: "#6c757d",
          dark: "#b0b3b8",
        },
        text: {
          light: "#212529",
          dark: "#f1f1f1",
        },
        muted: {
          light: "#6c757d",
          dark: "#a0a0a0",
        },
        border: {
          light: "#dee2e6",
          dark: "#2c2c2e",
        },
        danger: {
          light: "#dc3545",
          dark: "#ff4d4f",
        },
        warning: {
          light: "#ffc107",
          dark: "#ffc107",
        },
        success: {
          light: "#28a745",
          dark: "#52c41a",
        },
        light: {
          light: "#f8f9fa",
          dark: "#2a2a2a",
        },
        info: {
          light: "#6f42c1",
          dark: "#9b59b6",
        },
        navbar: {
          light: "#e9ecef",
          dark: "#1e2a3a",
        },
        sidebar: {
          light: "#f0f2f5",
          dark: "#1f1f1f",
        },
        sidebarHover: {
          light: "#e2e6ea",
          dark: "#253b63",
        },
        sidebarActive: {
          light: "#cce5ff",
          dark: "#4c6ef5",
        },
      },
    },
  },
  plugins: [],
};
