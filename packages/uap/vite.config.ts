import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";
import { fileURLToPath } from "url";

const packageRoot = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: {
        index: resolve(packageRoot, "src/index.ts"),
        tokens: resolve(packageRoot, "src/tokens/index.ts"),
        components: resolve(packageRoot, "src/components/index.ts"),
        runtime: resolve(packageRoot, "src/runtime/index.ts"),
        offline: resolve(packageRoot, "src/offline/index.ts"),
        device: resolve(packageRoot, "src/device/index.ts"),
        update: resolve(packageRoot, "src/update/index.ts"),
        marketplace: resolve(packageRoot, "src/marketplace/index.ts"),
        notifications: resolve(packageRoot, "src/notifications/index.ts"),
        printing: resolve(packageRoot, "src/printing/index.ts"),
        telemetry: resolve(packageRoot, "src/telemetry/index.ts"),
        sdk: resolve(packageRoot, "src/sdk/index.ts"),
        quality: resolve(packageRoot, "src/quality/index.ts"),
      },
      formats: ["es", "cjs"],
    },
    rollupOptions: {
      external: ["react", "react-dom", "react-router-dom"],
    },
    outDir: "dist",
  },
});
