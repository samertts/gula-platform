import { COOKIE_NAME, ONE_YEAR_MS, OAUTH_STATE_COOKIE, decodeOAuthState } from "@shared/const";
import { parse as parseCookieHeader } from "cookie";
import type { Express, Request, Response } from "express";
import * as db from "../db";
import { getSessionCookieOptions } from "./cookies";
import { sdk } from "./sdk";

function getQueryParam(req: Request, key: string): string | undefined {
  const value = req.query[key];
  return typeof value === "string" ? value : undefined;
}

const oauthBuckets = new Map<string, { count: number; resetAt: number }>();
const OAUTH_WINDOW_MS = 60_000;
const OAUTH_MAX_ATTEMPTS = 10;

function enforceOAuthRateLimit(req: Request, res: Response, next: () => void) {
  const now = Date.now();
  const key = req.ip || req.socket.remoteAddress || "unknown";
  const current = oauthBuckets.get(key);
  const bucket = !current || current.resetAt <= now
    ? { count: 0, resetAt: now + OAUTH_WINDOW_MS }
    : current;
  bucket.count += 1;
  oauthBuckets.set(key, bucket);
  if (oauthBuckets.size > 10_000) {
    oauthBuckets.forEach((value, bucketKey) => {
      if (value.resetAt <= now) oauthBuckets.delete(bucketKey);
    });
  }
  if (bucket.count > OAUTH_MAX_ATTEMPTS) {
    res.status(429).json({ error: "too many oauth attempts" });
    return;
  }
  next();
}

export function registerOAuthRoutes(app: Express) {
  app.get("/api/oauth/callback", enforceOAuthRateLimit, async (req: Request, res: Response) => {
    const code = getQueryParam(req, "code");
    const state = getQueryParam(req, "state");

    if (!code || !state || code.length > 4096 || state.length > 4096) {
      res.status(400).json({ error: "invalid oauth callback parameters" });
      return;
    }

    // CSRF guard: the nonce in `state` must match the one-time cookie that
    // startLogin set in the browser that began this login. An attacker can
    // forge `state`, but cannot plant this cookie in the victim's browser.
    let nonce: string | undefined;
    try {
      nonce = decodeOAuthState(state).nonce;
    } catch {
      res.status(403).json({ error: "invalid oauth state" });
      return;
    }
    const expectedNonce = parseCookieHeader(req.headers.cookie ?? "")[OAUTH_STATE_COOKIE];
    if (!nonce || nonce !== expectedNonce) {
      res.status(403).json({ error: "invalid oauth state" });
      return;
    }
    res.clearCookie(OAUTH_STATE_COOKIE, { path: "/", secure: true, sameSite: "none" });

    try {
      const tokenResponse = await sdk.exchangeCodeForToken(code, state);
      const userInfo = await sdk.getUserInfo(tokenResponse.accessToken);

      if (!userInfo.openId) {
        res.status(400).json({ error: "openId missing from user info" });
        return;
      }

      await db.upsertUser({
        openId: userInfo.openId,
        name: userInfo.name || null,
        email: userInfo.email ?? null,
        loginMethod: userInfo.loginMethod ?? userInfo.platform ?? null,
        lastSignedIn: new Date(),
      });

      const sessionToken = await sdk.createSessionToken(userInfo.openId, {
        name: userInfo.name || "",
        expiresInMs: ONE_YEAR_MS,
      });

      const cookieOptions = getSessionCookieOptions(req);
      res.cookie(COOKIE_NAME, sessionToken, { ...cookieOptions, maxAge: ONE_YEAR_MS });

      res.redirect(302, "/");
    } catch (error) {
      console.error("[OAuth] Callback failed", error);
      res.status(500).json({ error: "OAuth callback failed" });
    }
  });
}
