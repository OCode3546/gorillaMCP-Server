import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Relative asset paths so dist/ works from any sub-path (e.g. GitHub Pages).
  base: "./",
});
