
/*
==========================================================
NHOP SECURITY GUARDIAN (PRODUCTION SAFE)
Clinical Data Leak Prevention Layer
==========================================================
*/

import { useMedicalStore } from "../store/medical.store";

/* ======================================================
   INTERNAL STATE
====================================================== */

let initialized = false;

const ORIGINAL_FETCH = window.fetch.bind(window);

/* ======================================================
   CONFIG
====================================================== */

const ALLOWED_ORIGINS = new Set([
  location.origin,
  "http://localhost:3000"
]);

const SENSITIVE_KEYS = [
  "patient",
  "diagnosis",
  "result",
  "nationalId",
  "phone"
];

/* ======================================================
   SAFE SERIALIZE
====================================================== */

function safeStringify(obj: any): string {
  const seen = new WeakSet();

  return JSON.stringify(obj, (_, value) => {
    if (typeof value === "object" && value !== null) {
      if (seen.has(value)) return "[circular]";
      seen.add(value);
    }
    return value;
  });
}

/* ======================================================
   DETECTION
====================================================== */

function containsSensitiveData(payload: unknown): boolean {
  if (!payload) return false;

  try {
    const text = safeStringify(payload).toLowerCase();
    return SENSITIVE_KEYS.some(k => text.includes(k));
  } catch {
    return false;
  }
}

function isAllowed(url: string) {
  try {
    const parsed = new URL(url, location.origin);
    return ALLOWED_ORIGINS.has(parsed.origin);
  } catch {
    return false;
  }
}

/* ======================================================
   NETWORK GUARD
====================================================== */

function protectFetch() {

  window.fetch = async (
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> => {

    const url =
      typeof input === "string"
        ? input
        : input instanceof Request
        ? input.url
        : input.toString();

    const body = init?.body;

    if (!isAllowed(url) && containsSensitiveData(body)) {

      console.warn("🚨 NHOP BLOCKED DATA LEAK →", url);

      window.dispatchEvent(
        new CustomEvent("security:violation", {
          detail: { url, time: Date.now() }
        })
      );

      throw new Error("NHOP Security: request blocked");
    }

    return ORIGINAL_FETCH(input, init);
  };
}

/* ======================================================
   CONSOLE GUARD
====================================================== */

function wrapConsole(method: keyof Console) {

  const original = console[method].bind(console);

  console[method] = (...args: any[]) => {

    const sensitive = args;

    // يمكنك إضافة فلترة هنا لاحقاً
    // مثال:
    // if (sensitive.includes("token")) return;

    original(...args);
  };

}
