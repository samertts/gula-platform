import { defineConfig } from "vitest/config";

// A dedicated config, scoped to server/, is required: the repo root's
// vite.config.ts sets `root: "client"` (for the client/ SPA build), and
// vitest inherits that when it finds no other config in scope — so a bare
// `npx vitest` from the repo root silently only ever discovers client/
// tests, never server/'s. That's exactly why server/index.ts's demo-session
// security logic had zero test coverage despite the code existing: nothing
// in the default CI test invocation could ever have found a test file here.
export default defineConfig({
  test: {
    root: __dirname,
    include: ["tests/**/*.test.ts"],
    environment: "node",
  },
});
