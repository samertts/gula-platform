import type { Express } from "express";
import { ENV } from "./env";
import { normalizeKey, validateStorageUrl } from "../storage";

const storageBuckets = new Map<string, { count: number; resetAt: number }>();
const STORAGE_WINDOW_MS = 60_000;
const STORAGE_MAX_REQUESTS = 120;

export function registerStorageProxy(app: Express) {
  app.get("/manus-storage/*", async (req, res) => {
    const now = Date.now();
    const rateKey = req.ip || req.socket.remoteAddress || "unknown";
    const current = storageBuckets.get(rateKey);
    const bucket = !current || current.resetAt <= now
      ? { count: 0, resetAt: now + STORAGE_WINDOW_MS }
      : current;
    bucket.count += 1;
    storageBuckets.set(rateKey, bucket);
    if (bucket.count > STORAGE_MAX_REQUESTS) {
      res.status(429).send("Too many storage requests");
      return;
    }
    let key: string;
    try {
      const rawParam = (req.params as unknown as Record<string, string | string[]>)[0];
      const rawKey = Array.isArray(rawParam) ? rawParam.join("/") : rawParam ?? "";
      key = normalizeKey(rawKey);
    } catch {
      res.status(400).send("Invalid storage key");
      return;
    }
    if (!key) {
      res.status(400).send("Missing storage key");
      return;
    }

    if (!ENV.forgeApiUrl || !ENV.forgeApiKey) {
      res.status(500).send("Storage proxy not configured");
      return;
    }

    try {
      const forgeUrl = new URL(
        "v1/storage/presign/get",
        ENV.forgeApiUrl.replace(/\/+$/, "") + "/",
      );
      forgeUrl.searchParams.set("path", key);

      const forgeResp = await fetch(forgeUrl, {
        headers: { Authorization: `Bearer ${ENV.forgeApiKey}` },
      });

      if (!forgeResp.ok) {
        const body = await forgeResp.text().catch(() => "");
        console.error(`[StorageProxy] forge error: ${forgeResp.status} ${body}`);
        res.status(502).send("Storage backend error");
        return;
      }

      const { url: rawUrl } = (await forgeResp.json()) as { url: string };
      if (!rawUrl) {
        res.status(502).send("Empty signed URL from backend");
        return;
      }
      const url = validateStorageUrl(rawUrl);

      res.set("Cache-Control", "no-store");
      res.redirect(307, url);
    } catch (err) {
      console.error("[StorageProxy] failed:", err);
      res.status(502).send("Storage proxy error");
    }
  });
}
