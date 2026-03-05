
import { defineConfig } from "vite";
import path from "path";

export default defineConfig({
  resolve: {
    alias: {
      "@kernel": path.resolve(__dirname, "../nhop/kernel"),
      "@shared": path.resolve(__dirname, "../nhop/shared"),
    },
  },

  server: {
    fs: {
      allow: [".."],
    },
  },
});
