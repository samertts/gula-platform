import { GulsFailure, type PackManifest } from "./types";
import { extractPackArchive } from "./zip";

const HASH_RE = /^[a-f0-9]{64}$/;
const VERSION_RE = /^\d+\.\d+\.\d+$/;
const SAFE_PATH_RE =
  /^(catalogs|terminology|formatting|metadata|fonts)\/[A-Za-z0-9._/-]+$/;
const KEY_RE = /^[A-Za-z][A-Za-z0-9_-]*$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireString(
  value: unknown,
  field: string,
  pattern?: RegExp,
): string {
  if (
    typeof value !== "string" ||
    !value ||
    (pattern && !pattern.test(value))
  ) {
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", { field });
  }
  return value;
}

export function validateManifest(value: unknown): PackManifest {
  if (!isRecord(value))
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", { field: "root" });
  const files = value.files;
  if (!Array.isArray(files) || files.length === 0) {
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", { field: "files" });
  }
  const catalogs = value.catalogs;
  if (
    !Array.isArray(catalogs) ||
    catalogs.length === 0 ||
    catalogs.some((item) => typeof item !== "string")
  ) {
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", { field: "catalogs" });
  }
  const manifest: PackManifest = {
    schema_version: requireString(
      value.schema_version,
      "schema_version",
    ) as "1.0",
    language_id: requireString(value.language_id, "language_id", KEY_RE),
    locale_tag: requireString(value.locale_tag, "locale_tag"),
    native_name: requireString(value.native_name, "native_name"),
    fallback_locale: requireString(
      value.fallback_locale,
      "fallback_locale",
    ) as "en",
    pack_version: requireString(value.pack_version, "pack_version", VERSION_RE),
    minimum_engine_version: requireString(
      value.minimum_engine_version,
      "minimum_engine_version",
      VERSION_RE,
    ),
    direction: requireString(value.direction, "direction") as "rtl" | "ltr",
    script: requireString(value.script, "script", /^[A-Z][a-z]{3}$/),
    catalogs: catalogs as string[],
    terminology_version: requireString(
      value.terminology_version,
      "terminology_version",
      VERSION_RE,
    ),
    content_hash: requireString(value.content_hash, "content_hash", HASH_RE),
    content_size:
      typeof value.content_size === "number" && value.content_size >= 0
        ? value.content_size
        : -1,
    publisher: requireString(value.publisher, "publisher"),
    signer_key_id: requireString(
      value.signer_key_id,
      "signer_key_id",
      /^[A-Za-z0-9._:-]+$/,
    ),
    approval_status: requireString(
      value.approval_status,
      "approval_status",
    ) as PackManifest["approval_status"],
    created_at: requireString(value.created_at, "created_at"),
    files: files.map((entry) => {
      if (!isRecord(entry))
        throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", { field: "files" });
      return {
        path: requireString(entry.path, "path", SAFE_PATH_RE),
        sha256: requireString(entry.sha256, "sha256", HASH_RE),
        size:
          typeof entry.size === "number" && entry.size >= 0 ? entry.size : -1,
      };
    }),
    signature: requireString(
      value.signature,
      "signature",
      /^[A-Za-z0-9+/]+={0,2}$/,
    ),
  };
  if (manifest.schema_version !== "1.0" || manifest.fallback_locale !== "en") {
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", {
      field: "schema_version",
    });
  }
  if (manifest.direction !== "rtl" && manifest.direction !== "ltr") {
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", { field: "direction" });
  }
  if (
    manifest.approval_status !== "approved" &&
    manifest.approval_status !== "synthetic_test_only"
  ) {
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", {
      field: "approval_status",
    });
  }
  if (
    manifest.content_size < 0 ||
    manifest.files.some((entry) => entry.size < 0)
  ) {
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", { field: "sizes" });
  }
  const paths = manifest.files.map((entry) => entry.path);
  if (
    new Set(paths).size !== paths.length ||
    paths.some((path) => path.includes("..") || path.startsWith("/"))
  ) {
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", {
      field: "file_paths",
    });
  }
  return manifest;
}

export async function sha256(bytes: Uint8Array): Promise<string> {
  if (!globalThis.crypto?.subtle)
    throw new GulsFailure("GULS_PACK_UNSUPPORTED", {
      reason: "web_crypto_unavailable",
    });
  const digest = await globalThis.crypto.subtle.digest(
    "SHA-256",
    bytes as BufferSource,
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

export async function contentHash(
  files: Record<string, Uint8Array>,
): Promise<string> {
  const parts: string[] = [];
  for (const path of Object.keys(files).sort()) {
    if (path === "manifest.json") continue;
    const digest = await sha256(files[path] ?? new Uint8Array());
    parts.push(`${path}:${digest}:${files[path]?.length ?? 0}\n`);
  }
  return sha256(new TextEncoder().encode(parts.join("")));
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (isRecord(value)) {
    const sorted: Record<string, unknown> = {};
    for (const key of Object.keys(value).sort())
      sorted[key] = canonicalize(value[key]);
    return sorted;
  }
  return value;
}

function base64ToBytes(value: string): Uint8Array {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1)
    bytes[index] = binary.charCodeAt(index);
  return bytes;
}

export async function verifySignature(
  manifest: PackManifest,
  publicKey: Uint8Array,
): Promise<void> {
  if (!globalThis.crypto?.subtle)
    throw new GulsFailure("GULS_PACK_UNSUPPORTED", {
      reason: "web_crypto_unavailable",
    });
  const payload: Record<string, unknown> = { ...manifest } as Record<
    string,
    unknown
  >;
  delete payload.signature;
  const bytes = new TextEncoder().encode(JSON.stringify(canonicalize(payload)));
  try {
    const key = await globalThis.crypto.subtle.importKey(
      "raw",
      publicKey as BufferSource,
      { name: "Ed25519" },
      false,
      ["verify"],
    );
    const valid = await globalThis.crypto.subtle.verify(
      "Ed25519",
      key,
      base64ToBytes(manifest.signature) as BufferSource,
      bytes,
    );
    if (!valid) throw new GulsFailure("GULS_PACK_SIGNATURE_INVALID");
  } catch (error) {
    if (error instanceof GulsFailure) throw error;
    throw new GulsFailure("GULS_PACK_SIGNATURE_INVALID", {
      reason: "verification_unavailable",
    });
  }
}

function compareVersions(left: string, right: string): number {
  const parse = (value: string) => value.split(".").map((part) => Number(part));
  const a = parse(left);
  const b = parse(right);
  for (let index = 0; index < 3; index += 1) {
    if ((a[index] ?? 0) !== (b[index] ?? 0))
      return (a[index] ?? 0) - (b[index] ?? 0);
  }
  return 0;
}

export interface VerifyOptions {
  languageId: string;
  localeTag: string;
  direction: "rtl" | "ltr";
  script: string;
  engineVersion: string;
  publicKey: Uint8Array;
  allowSynthetic: boolean;
  syntheticSignerKeyId?: string;
  expectedHash?: string | null;
}

export interface VerifiedPack {
  manifest: PackManifest;
  files: Record<string, Uint8Array>;
  contentHash: string;
}

/** Verify a pack entirely on the client before any activation. */
export async function verifyPack(
  packBytes: Uint8Array,
  options: VerifyOptions,
): Promise<VerifiedPack> {
  const files = await extractPackArchive(packBytes);
  const manifestBytes = files["manifest.json"];
  if (!manifestBytes)
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", {
      field: "manifest.json",
    });
  let manifest: PackManifest;
  try {
    manifest = validateManifest(
      JSON.parse(new TextDecoder().decode(manifestBytes)) as unknown,
    );
  } catch (error) {
    if (error instanceof GulsFailure) throw error;
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", {
      reason: "parse_failed",
    });
  }
  if (manifest.language_id !== options.languageId)
    throw new GulsFailure("GULS_PACK_POLICY_REJECTED", {
      reason: "language_mismatch",
    });
  if (manifest.locale_tag !== options.localeTag)
    throw new GulsFailure("GULS_PACK_POLICY_REJECTED", {
      reason: "locale_mismatch",
    });
  if (
    manifest.direction !== options.direction ||
    manifest.script !== options.script
  ) {
    throw new GulsFailure("GULS_PACK_POLICY_REJECTED", {
      reason: "script_or_direction_mismatch",
    });
  }
  if (
    compareVersions(options.engineVersion, manifest.minimum_engine_version) < 0
  ) {
    throw new GulsFailure("GULS_PACK_INCOMPATIBLE", {
      required: manifest.minimum_engine_version,
    });
  }
  if (manifest.approval_status === "synthetic_test_only") {
    if (!options.allowSynthetic)
      throw new GulsFailure("GULS_PACK_POLICY_REJECTED", {
        reason: "synthetic_disabled",
      });
    if (
      !options.syntheticSignerKeyId ||
      manifest.signer_key_id !== options.syntheticSignerKeyId
    ) {
      throw new GulsFailure("GULS_PACK_POLICY_REJECTED", {
        reason: "synthetic_key_mismatch",
      });
    }
  }
  const actualCatalogs = Object.keys(files)
    .map((path) => /^catalogs\/([a-z][a-z0-9_]*)\.json$/.exec(path)?.[1])
    .filter((value): value is string => Boolean(value));
  if (
    new Set(actualCatalogs).size !== actualCatalogs.length ||
    new Set(actualCatalogs).size !== new Set(manifest.catalogs).size ||
    actualCatalogs.some((value) => !manifest.catalogs.includes(value))
  ) {
    throw new GulsFailure("GULS_PACK_POLICY_REJECTED", {
      reason: "catalog_mismatch",
    });
  }
  if (actualCatalogs.includes("clinical")) {
    throw new GulsFailure("GULS_PACK_POLICY_REJECTED", {
      reason: "clinical_catalog_not_permitted_in_dynamic_pack",
    });
  }
  for (const entry of manifest.files) {
    const content = files[entry.path];
    if (
      !content ||
      content.length !== entry.size ||
      (await sha256(content)) !== entry.sha256
    ) {
      throw new GulsFailure("GULS_PACK_HASH_MISMATCH", { path: entry.path });
    }
  }
  const computed = await contentHash(files);
  if (computed !== manifest.content_hash)
    throw new GulsFailure("GULS_PACK_HASH_MISMATCH", {
      reason: "content_hash",
    });
  if (options.expectedHash && options.expectedHash !== manifest.content_hash) {
    throw new GulsFailure("GULS_PACK_HASH_MISMATCH", {
      reason: "expected_hash",
    });
  }
  const actualSize = Object.entries(files)
    .filter(([path]) => path !== "manifest.json")
    .reduce((total, [, content]) => total + (content?.length ?? 0), 0);
  if (actualSize !== manifest.content_size)
    throw new GulsFailure("GULS_PACK_MANIFEST_INVALID", {
      field: "content_size",
    });
  await verifySignature(manifest, options.publicKey);
  return { manifest, files, contentHash: computed };
}
