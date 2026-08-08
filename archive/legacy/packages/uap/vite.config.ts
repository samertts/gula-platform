import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: {
        index: resolve(__dirname, "src/index.ts"),
        tokens: resolve(__dirname, "src/tokens/index.ts"),
        components: resolve(__dirname, "src/components/index.ts"),
        runtime: resolve(__dirname, "src/runtime/index.ts"),
        offline: resolve(__dirname, "src/offline/index.ts"),
        device: resolve(__dirname, "src/device/index.ts"),
        update: resolve(__dirname, "src/update/index.ts"),
        marketplace: resolve(__dirname, "src/marketplace/index.ts"),
        notifications: resolve(__dirname, "src/notifications/index.ts"),
        printing: resolve(__dirname, "src/printing/index.ts"),
        telemetry: resolve(__dirname, "src/telemetry/index.ts"),
        sdk: resolve(__dirname, "src/sdk/index.ts"),
        quality: resolve(__dirname, "src/quality/index.ts"),
      },
      formats: ["es", "cjs"],
    },
    rollupOptions: {
      external: ["react", "react-dom", "react-router-dom"],
    },
    outDir: "dist",
  },
});
