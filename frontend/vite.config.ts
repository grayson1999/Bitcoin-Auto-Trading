import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const VITE_DEV_PORT = 5173;
const API_BASE_URL = "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: VITE_DEV_PORT,
    proxy: {
      "/api": {
        target: API_BASE_URL,
        changeOrigin: true,
      },
    },
  },
});
