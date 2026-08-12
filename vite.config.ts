import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  root: path.resolve(__dirname, "client"),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "client/src"),
      "@components": path.resolve(__dirname, "client/src/components"),
      "@pages": path.resolve(__dirname, "client/src/pages"),
      "@lib": path.resolve(__dirname, "client/src/lib"),
      "@hooks": path.resolve(__dirname, "client/src/hooks"),
      "@contexts": path.resolve(__dirname, "client/src/contexts"),
    },
  },
  build: {
    outDir: path.resolve(__dirname, "dist/client"),
    emptyOutDir: true,
    sourcemap: true,
  },
  server: {
    // Allows the temporary development preview hostname; it does not affect the production build.
    allowedHosts: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:3000",
        changeOrigin: true,
      },
    },
  },
});
