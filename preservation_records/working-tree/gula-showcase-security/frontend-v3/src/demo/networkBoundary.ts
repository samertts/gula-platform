/**
 * Centralized Showcase network/data boundary.
 *
 * While a Showcase session is active, ALL network access from the browser is
 * blocked — not only requests through the shared API client. This covers:
 *   - the shared axios client (primary guard, in api/client.ts)
 *   - any raw axios / XHR usage (e.g. the token-refresh path)
 *   - any raw fetch() usage
 *
 * The guard is transparent whenever no Showcase session is active, so it has
 * zero effect on production login/APIs. It is installed once at module load
 * and stays installed: it only activates while isDemoSessionActive() is true.
 *
 * Showcase code itself performs NO network calls (synthetic data only), so
 * this boundary is defense-in-depth on top of the interceptor.
 */

import { isDemoSessionActive } from "./session";

export class ShowcaseNetworkBlockedError extends Error {
  constructor() {
    super("Showcase network access is blocked (demo session is read-only)");
    this.name = "ShowcaseNetworkBlockedError";
  }
}

export function assertNetworkAllowed(): void {
  if (isDemoSessionActive()) {
    throw new ShowcaseNetworkBlockedError();
  }
}

let fetchPatched = false;
let xhrPatched = false;
let originalFetch: typeof globalThis.fetch | undefined;
let originalXhrOpen: ((...args: unknown[]) => unknown) | undefined;

/** Installs the global fetch / XHR guard. Idempotent. Safe to call repeatedly. */
export function installShowcaseNetworkGuard(): void {
  if (typeof globalThis === "undefined") return;

  if (!fetchPatched && typeof globalThis.fetch === "function") {
    originalFetch = globalThis.fetch;
    globalThis.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
      assertNetworkAllowed();
      return originalFetch!(input, init);
    }) as typeof fetch;
    fetchPatched = true;
  }

  if (!xhrPatched && typeof globalThis.XMLHttpRequest !== "undefined") {
    const proto = globalThis.XMLHttpRequest.prototype;
    originalXhrOpen = proto.open;
    proto.open = function (this: XMLHttpRequest, ...args: Parameters<XMLHttpRequest["open"]>) {
      assertNetworkAllowed();
      return (originalXhrOpen as (this: XMLHttpRequest, ...a: never[]) => unknown).apply(this, args as never[]);
    };
    xhrPatched = true;
  }
}

/** Removes the global fetch / XHR guard. Idempotent. */
export function uninstallShowcaseNetworkGuard(): void {
  if (typeof globalThis === "undefined") return;

  if (fetchPatched && originalFetch) {
    globalThis.fetch = originalFetch;
    fetchPatched = false;
  }

  if (xhrPatched && originalXhrOpen && typeof globalThis.XMLHttpRequest !== "undefined") {
    globalThis.XMLHttpRequest.prototype.open = originalXhrOpen as typeof XMLHttpRequest.prototype.open;
    xhrPatched = false;
  }
}

installShowcaseNetworkGuard();
