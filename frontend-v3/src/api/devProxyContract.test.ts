/**
 * The dev server must be the same system as production.
 *
 * The API client's base URL is `/api`. In production the gateway serves that
 * prefix with
 *
 *     location /api/ { proxy_pass http://gula_backend/; }
 *
 * and the trailing slash on `proxy_pass` strips `/api` before the request
 * reaches the backend. So the literal paths in endpoints.ts are the paths the
 * backend serves, and the `/api`-prefixed subtree is reached as `/api/api/...`.
 *
 * The dev proxy had no matching rewrite, so `npm run dev` forwarded
 * `/api/login` unchanged and the backend answered 404 -- for every live-mode
 * call, not just login. Measured against a real backend: 5 of 5 probed paths
 * returned 404 through the dev server and 401/405/422 straight at the backend.
 *
 * These tests hold the two servers to the same contract.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import viteConfig from "../../vite.config";

type ProxyEntry = { target?: string; rewrite?: (path: string) => string };

const proxy = (viteConfig as { server?: { proxy?: Record<string, ProxyEntry> } }).server?.proxy;

const apiEntry = proxy?.["/api"];

/** Every path literal the API client asks for, read from the source of truth. */
function declaredEndpointPaths(): string[] {
  // vitest runs with the project root as cwd; import.meta.url is not a file
  // URL under the test environment, so resolve from the root instead.
  const source = readFileSync(resolve(process.cwd(), "src/api/endpoints.ts"), "utf8");
  const found = source.match(/"\/[a-zA-Z0-9/_{}$.-]*"/g) ?? [];
  return [...new Set(found.map((literal) => literal.slice(1, -1)))];
}

describe("dev proxy contract", () => {
  it("declares a proxy entry for the API client's base URL", () => {
    expect(apiEntry).toBeDefined();
    expect(apiEntry?.target).toContain("8000");
  });

  it("strips /api exactly as the production gateway does", () => {
    expect(apiEntry?.rewrite).toBeTypeOf("function");
    expect(apiEntry?.rewrite?.("/api/login")).toBe("/login");
    expect(apiEntry?.rewrite?.("/api/patients")).toBe("/patients");
    expect(apiEntry?.rewrite?.("/api/admin/labs")).toBe("/admin/labs");
  });

  it("leaves the genuinely /api-prefixed subtree intact", () => {
    // The client asks for "/api/ai/chat" against base "/api", so the request
    // arrives as "/api/api/ai/chat" and must reach the backend as
    // "/api/ai/chat" -- one prefix stripped, not both.
    expect(apiEntry?.rewrite?.("/api/api/ai/chat")).toBe("/api/ai/chat");
    expect(apiEntry?.rewrite?.("/api/api/ai/v2/cds/evaluate")).toBe("/api/ai/v2/cds/evaluate");
  });

  it("is transparent for every endpoint the client declares", () => {
    const paths = declaredEndpointPaths();
    // Positive control: an empty list would make the loop below vacuous.
    expect(paths.length).toBeGreaterThan(100);

    const broken = paths.filter((path) => apiEntry?.rewrite?.(`/api${path}`) !== path);
    expect(broken).toEqual([]);
  });

  it("does not rewrite paths that were never prefixed", () => {
    // A rewrite that stripped /api anywhere in the path, rather than only at
    // the front, would corrupt these. Guards against a greedy replace.
    expect(apiEntry?.rewrite?.("/api/labs/api/status")).toBe("/labs/api/status");
  });
});
