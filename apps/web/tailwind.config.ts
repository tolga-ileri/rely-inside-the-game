import type { Config } from "tailwindcss";

// Rely visual identity: orange accent (#F26522 / dark #FF6B2C), neutral ink scale, dark broadcast shell.
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        rely: { 50: "#FFF6F0", 100: "#FFE7D6", 400: "#FF8A52", 500: "#FF6B2C", 600: "#F26522", 700: "#C24A12" },
        shell: { 950: "#0B0E13", 900: "#11151C", 850: "#161B23", 800: "#1C222C", 700: "#262D39", 600: "#323B4A" },
        ink: { 50: "#F5F7FA", 200: "#D5DBE3", 300: "#AEB7C4", 400: "#8792A2", 500: "#667085" },
        pitch: { 700: "#1F5F2E", 600: "#25703A", 500: "#2C7F43" },
        positive: "#3FB97A",
        warn: "#E8B03D",
        risk: "#F0645A",
        info: "#5AA9F0",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "-apple-system", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Consolas", "monospace"],
      },
      fontSize: { meta: ["12px", { lineHeight: "16px" }], dense: ["13px", { lineHeight: "18px" }] },
      borderRadius: { xl: "10px", "2xl": "12px" },
    },
  },
  plugins: [],
};
export default config;
