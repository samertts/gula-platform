import { getLanguage } from "../registry";
import {
  resolveLanguage,
  translateKey,
  type Resolution,
  type TranslationResult,
} from "../runtime";
import { contentHash, type VerifiedPack } from "./verify";
import {
  GulsFailure,
  type InstalledPackRecord,
  type StorageDriver,
} from "./types";

export const GULS_ENGINE_VERSION = "1.0.0";

/** English is bundled with the application and is always available offline. */
export const BUNDLED_FALLBACK_LANGUAGE = "en";

export async function readyLanguageIds(
  storage: StorageDriver,
): Promise<Set<string>> {
  const ready = new Set(await storage.listReady());
  ready.add(BUNDLED_FALLBACK_LANGUAGE);
  return ready;
}

export async function verifyStoredRecord(
  record: InstalledPackRecord,
): Promise<boolean> {
  if (!record.manifest || !record.files) return false;
  try {
    return (await contentHash(record.files)) === record.contentHash;
  } catch {
    return false;
  }
}

/** Resolve a language using only locally stored, verified packs. */
export async function resolveOffline(
  requested: string | null | undefined,
  storage: StorageDriver,
  preferred?: string | null,
): Promise<Resolution> {
  return resolveLanguage(requested, await readyLanguageIds(storage), preferred);
}

/** Atomically activate a verified pack while preserving the previous version. */
export async function activatePack(
  storage: StorageDriver,
  verified: VerifiedPack,
  requestedLanguageId: string,
): Promise<InstalledPackRecord> {
  if (verified.manifest.language_id !== requestedLanguageId) {
    throw new GulsFailure("GULS_PACK_POLICY_REJECTED", {
      reason: "language_mismatch",
    });
  }
  const textFiles: Record<string, Uint8Array> = {};
  for (const [path, content] of Object.entries(verified.files)) {
    textFiles[path] = content;
  }
  const record: InstalledPackRecord = {
    languageId: requestedLanguageId,
    packVersion: verified.manifest.pack_version,
    contentHash: verified.contentHash,
    manifest: verified.manifest,
    files: textFiles,
    installedAt: new Date().toISOString(),
  };
  await storage.activate(record);
  return record;
}

/** Detect cache corruption after a browser restart and restore the last good pack. */
export async function recoverPack(
  storage: StorageDriver,
  languageId: string,
): Promise<InstalledPackRecord | undefined> {
  const active = await storage.getActive(languageId);
  if (active && (await verifyStoredRecord(active))) return active;
  const restored = await storage.rollback(languageId);
  if (!restored) {
    if (active) await storage.disable(languageId);
    return undefined;
  }
  const previous = await storage.getActive(languageId);
  if (previous && (await verifyStoredRecord(previous))) return previous;
  if (previous) await storage.disable(languageId);
  return undefined;
}

/** Look up a translation from a stored catalog without any network access. */
export async function translateOffline(
  storage: StorageDriver,
  languageId: string,
  fallbackCatalog: Readonly<Record<string, string>>,
  key: string,
  parameters: Record<string, string | number> = {},
): Promise<TranslationResult> {
  const record =
    (await storage.getActive(languageId)) ??
    (await recoverPack(storage, languageId));
  if (!record) return translateKey({}, fallbackCatalog, key, parameters);
  const catalogFile = `catalogs/common.json`;
  const bytes = record.files[catalogFile];
  if (!bytes) return translateKey({}, fallbackCatalog, key, parameters);
  try {
    const catalog = JSON.parse(new TextDecoder().decode(bytes)) as Record<
      string,
      string
    >;
    return translateKey(catalog, fallbackCatalog, key, parameters);
  } catch {
    return translateKey({}, fallbackCatalog, key, parameters);
  }
}

/** Guard against silently publishing a language whose registry entry is blocked. */
export function assertPublishable(languageId: string): void {
  const definition = getLanguage(languageId);
  if (
    !definition ||
    !definition.is_active ||
    !definition.is_publishable ||
    definition.approval_status !== "approved"
  ) {
    throw new GulsFailure("GULS_PACK_POLICY_REJECTED", {
      language_id: languageId,
    });
  }
}
