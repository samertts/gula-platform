/**
 * GULA Edge Worker — authentication + audit + bot-gate
 *
 * Runs at Cloudflare's edge in front of the origin (HAProxy → gula-backend).
 *
 * Responsibilities:
 *   1. Country allow-list (ISO codes) + Tor/known-bad-ASN deny-list
 *   2. Reject requests that carry no User-Agent (script scrapers)
 *   3. Stamp an HMAC-signed header so the origin can verify the request
 *      came through Cloudflare and not directly from a leaked origin IP
 *   4. Attach a deterministic request-id for cross-stack tracing
 *   5. Minimal per-IP burst limiter (Workers KV is optional; not wired here
 *      because Cloudflare's own rate-limit rules handle the primary burst —
 *      this Worker exists for defence-in-depth, not primary rate-limit).
 *
 * Secrets expected:
 *   CF_ORIGIN_URL      — e.g. "https://origin.gula.health"
 *   CF_SHARED_SECRET   — rotating secret; the origin checks
 *                        x-cf-signed against HMAC-SHA256(path, secret)
 */

const ALLOWED_COUNTRIES = ["IQ", "SA", "AE", "JO", "LB", "EG", "TR", "US", "DE"];
const BLOCKED_ASN_PATTERNS = [/^AS14061$/, /tor/i]; // placeholders

function newRequestId() {
  // 16-byte random hex, collision-safe for tracing
  const b = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(b, x => x.toString(16).padStart(2, "0")).join("");
}

async function signPath(path, secret) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(path));
  return Array.from(new Uint8Array(sig), x => x.toString(16).padStart(2, "0")).join("");
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // ── 1. Country allow-list ────────────────────────────────────────────
    const country = request.cf && request.cf.country;
    if (country && !ALLOWED_COUNTRIES.includes(country)) {
      return new Response("geo-blocked", { status: 451 });
    }

    // ── 2. ASN deny-list ─────────────────────────────────────────────────
    const asn = (request.cf && request.cf.asOrganization) || "";
    if (BLOCKED_ASN_PATTERNS.some(rx => rx.test(asn))) {
      return new Response("blocked", { status: 403 });
    }

    // ── 3. User-Agent gate ───────────────────────────────────────────────
    const ua = request.headers.get("user-agent") || "";
    if (ua.length < 5) {
      return new Response("no user-agent", { status: 400 });
    }

    // ── 4. Build signed request to origin ────────────────────────────────
    const rid = newRequestId();
    const path = url.pathname + url.search;
    const sig = await signPath(path, env.CF_SHARED_SECRET);

    const headers = new Headers(request.headers);
    headers.set("x-request-id", rid);
    headers.set("x-cf-country", country || "??");
    headers.set("x-cf-asn", asn);
    headers.set("x-cf-signed", sig);
    headers.delete("cf-connecting-ip"); // origin reads x-forwarded-for

    const originUrl = new URL(env.CF_ORIGIN_URL);
    originUrl.pathname = url.pathname;
    originUrl.search = url.search;

    const upstream = new Request(originUrl.toString(), {
      method: request.method,
      headers,
      body: request.body,
      redirect: "manual",
    });

    const response = await fetch(upstream);

    // ── 5. Strip origin-leaking headers on the way back out ──────────────
    const out = new Response(response.body, response);
    out.headers.delete("server");
    out.headers.delete("x-powered-by");
    out.headers.set("x-request-id", rid);
    out.headers.set("strict-transport-security", "max-age=63072000; includeSubDomains; preload");
    out.headers.set("referrer-policy", "strict-origin-when-cross-origin");
    return out;
  },
};
