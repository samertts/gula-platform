import { webcrypto } from "node:crypto";
import { describe, expect, it } from "vitest";
import {
  checkTransferPolicy,
  downloadPack,
  GulsFailure,
  MemoryPackStorage,
  verifyPack,
  verifyStoredRecord,
  activatePack,
  recoverPack,
  resolveOffline,
  type PackManifest,
  type StagingRecord,
} from "./index";

const encoder = new TextEncoder();

function crc32(bytes: Uint8Array): number {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1)
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function writeU16(view: DataView, offset: number, value: number): void {
  view.setUint16(offset, value, true);
}

function writeU32(view: DataView, offset: number, value: number): void {
  view.setUint32(offset, value, true);
}

function makeZip(
  files: Record<string, Uint8Array> | Array<[string, Uint8Array]>,
): Uint8Array {
  const entries = Array.isArray(files) ? files : Object.entries(files);
  const locals: Uint8Array[] = [];
  const centrals: Uint8Array[] = [];
  let offset = 0;
  for (const [name, content] of entries) {
    const nameBytes = encoder.encode(name);
    const checksum = crc32(content);
    const local = new Uint8Array(30 + nameBytes.length + content.length);
    const localView = new DataView(local.buffer);
    writeU32(localView, 0, 0x04034b50);
    writeU16(localView, 4, 20);
    writeU32(localView, 14, checksum);
    writeU32(localView, 18, content.length);
    writeU32(localView, 22, content.length);
    writeU16(localView, 26, nameBytes.length);
    local.set(nameBytes, 30);
    local.set(content, 30 + nameBytes.length);
    locals.push(local);

    const central = new Uint8Array(46 + nameBytes.length);
    const centralView = new DataView(central.buffer);
    writeU32(centralView, 0, 0x02014b50);
    writeU16(centralView, 4, 20);
    writeU16(centralView, 6, 20);
    writeU32(centralView, 16, checksum);
    writeU32(centralView, 20, content.length);
    writeU32(centralView, 24, content.length);
    writeU16(centralView, 28, nameBytes.length);
    writeU32(centralView, 42, offset);
    central.set(nameBytes, 46);
    centrals.push(central);
    offset += local.length;
  }
  const centralSize = centrals.reduce(
    (total, entry) => total + entry.length,
    0,
  );
  const end = new Uint8Array(22);
  const endView = new DataView(end.buffer);
  writeU32(endView, 0, 0x06054b50);
  writeU16(endView, 8, centrals.length);
  writeU16(endView, 10, centrals.length);
  writeU32(endView, 12, centralSize);
  writeU32(endView, 16, offset);
  return new Uint8Array([
    ...locals.flatMap((entry) => Array.from(entry)),
    ...centrals.flatMap((entry) => Array.from(entry)),
    ...end,
  ]);
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (value && typeof value === "object") {
    const sorted: Record<string, unknown> = {};
    for (const key of Object.keys(value).sort())
      sorted[key] = canonicalize((value as Record<string, unknown>)[key]);
    return sorted;
  }
  return value;
}

async function toHex(bytes: Uint8Array): Promise<string> {
  const digest = await webcrypto.subtle.digest(
    "SHA-256",
    bytes as BufferSource,
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

interface Fixture {
  pack: Uint8Array;
  publicKey: Uint8Array;
  manifest: PackManifest;
  files: Record<string, Uint8Array>;
}

async function makeFixture(
  options: {
    catalogs?: string[];
    languageId?: string;
    includeClinicalCatalog?: boolean;
  } = {},
): Promise<Fixture> {
  const keys = await webcrypto.subtle.generateKey({ name: "Ed25519" }, true, [
    "sign",
    "verify",
  ]);
  const publicKey = new Uint8Array(
    await webcrypto.subtle.exportKey("raw", keys.publicKey),
  );
  const files: Record<string, Uint8Array> = {
    "catalogs/common.json": encoder.encode('{"ui.home":"Synthetic home"}'),
    "metadata/README.md": encoder.encode("Synthetic test pack."),
  };
  if (options.includeClinicalCatalog) {
    files["catalogs/clinical.json"] = encoder.encode(
      '{"clinical.allergy":"Synthetic clinical term"}',
    );
  }
  const parts: string[] = [];
  for (const path of Object.keys(files).sort())
    parts.push(`${path}:${await toHex(files[path]!)}:${files[path]!.length}\n`);
  const contentHash = await toHex(encoder.encode(parts.join("")));
  const fileEntries = await Promise.all(
    Object.entries(files).map(async ([path, content]) => ({
      path,
      sha256: await toHex(content),
      size: content.length,
    })),
  );
  const manifest: Omit<PackManifest, "signature"> = {
    schema_version: "1.0",
    language_id: options.languageId ?? "fa",
    locale_tag: "fa-IR",
    native_name: "Synthetic Persian",
    fallback_locale: "en",
    pack_version: "1.0.0",
    minimum_engine_version: "1.0.0",
    direction: "rtl",
    script: "Arab",
    catalogs: options.catalogs ?? ["common"],
    terminology_version: "1.0.0",
    content_hash: contentHash,
    content_size: Object.values(files).reduce(
      (total, content) => total + content.length,
      0,
    ),
    publisher: "GULA Synthetic Tests",
    signer_key_id: "synthetic-test-key",
    approval_status: "synthetic_test_only",
    created_at: "2026-01-01T00:00:00Z",
    files: fileEntries,
  };
  const signature = await webcrypto.subtle.sign(
    "Ed25519",
    keys.privateKey,
    encoder.encode(JSON.stringify(canonicalize(manifest))) as BufferSource,
  );
  const signed: PackManifest = {
    ...manifest,
    signature: Buffer.from(signature).toString("base64"),
  };
  const archive = makeZip({
    "manifest.json": encoder.encode(JSON.stringify(signed)),
    ...files,
  });
  return { pack: archive, publicKey, manifest: signed, files };
}

const verifyOptions = (publicKey: Uint8Array) => ({
  languageId: "fa",
  localeTag: "fa-IR",
  direction: "rtl" as const,
  script: "Arab",
  engineVersion: "1.0.0",
  publicKey,
  allowSynthetic: true,
  syntheticSignerKeyId: "synthetic-test-key",
});

describe("GULS offline pack verification", () => {
  it("accepts a valid signed synthetic pack", async () => {
    const fixture = await makeFixture();
    const verified = await verifyPack(
      fixture.pack,
      verifyOptions(fixture.publicKey),
    );
    expect(verified.manifest.language_id).toBe("fa");
    expect(verified.files["catalogs/common.json"]).toBeDefined();
  });

  it("rejects modified content after signing", async () => {
    const fixture = await makeFixture();
    const tampered = makeZip({
      "manifest.json": encoder.encode(JSON.stringify(fixture.manifest)),
      "catalogs/common.json": encoder.encode('{"ui.home":"Tampered"}'),
      "metadata/README.md": fixture.files["metadata/README.md"]!,
    });
    await expect(
      verifyPack(tampered, verifyOptions(fixture.publicKey)),
    ).rejects.toMatchObject({
      code: "GULS_PACK_HASH_MISMATCH",
    });
  });

  it("rejects a pack signed by an untrusted key", async () => {
    const fixture = await makeFixture();
    const other = await webcrypto.subtle.generateKey(
      { name: "Ed25519" },
      true,
      ["sign", "verify"],
    );
    const wrongKey = new Uint8Array(
      await webcrypto.subtle.exportKey("raw", other.publicKey),
    );
    await expect(
      verifyPack(fixture.pack, verifyOptions(wrongKey)),
    ).rejects.toMatchObject({
      code: "GULS_PACK_SIGNATURE_INVALID",
    });
  });

  it("rejects a clinical catalog in a dynamic pack", async () => {
    const fixture = await makeFixture({
      catalogs: ["common", "clinical"],
      includeClinicalCatalog: true,
    });
    await expect(
      verifyPack(fixture.pack, verifyOptions(fixture.publicKey)),
    ).rejects.toMatchObject({
      code: "GULS_PACK_POLICY_REJECTED",
      parameters: { reason: "clinical_catalog_not_permitted_in_dynamic_pack" },
    });
  });

  it("rejects path traversal in archive members", async () => {
    const traversal = makeZip({
      "catalogs/../../evil.json": encoder.encode("{}"),
    });
    await expect(
      verifyPack(traversal, verifyOptions(new Uint8Array(32))),
    ).rejects.toMatchObject({
      code: "GULS_PACK_UNSAFE_PATH",
    });
  });

  it("rejects archives that are too short to contain an EOCD", async () => {
    await expect(
      verifyPack(new Uint8Array([1, 2, 3]), verifyOptions(new Uint8Array(32))),
    ).rejects.toMatchObject({
      code: "GULS_PACK_INVALID_ARCHIVE",
      parameters: { reason: "archive_too_short" },
    });
  });

  it("rejects archives with more than 256 members", async () => {
    const members: Array<[string, Uint8Array]> = Array.from(
      { length: 257 },
      (_, index) =>
        [`metadata/file-${index}.json`, encoder.encode("{}")] as [
          string,
          Uint8Array,
        ],
    );
    await expect(
      verifyPack(makeZip(members), verifyOptions(new Uint8Array(32))),
    ).rejects.toMatchObject({
      code: "GULS_PACK_INVALID_ARCHIVE",
      parameters: { reason: "too_many_members", count: 257 },
    });
  });

  it("rejects duplicate archive member names", async () => {
    const duplicate = makeZip([
      ["metadata/duplicate.json", encoder.encode("{}")],
      ["metadata/duplicate.json", encoder.encode("{}")],
    ]);
    await expect(
      verifyPack(duplicate, verifyOptions(new Uint8Array(32))),
    ).rejects.toMatchObject({
      code: "GULS_PACK_INVALID_ARCHIVE",
      parameters: {
        reason: "duplicate_member",
        path: "metadata/duplicate.json",
      },
    });
  });
});

describe("GULS offline storage and recovery", () => {
  it("preserves the previous version on activation and can roll back", async () => {
    const storage = new MemoryPackStorage();
    const first = await makeFixture();
    const verifiedFirst = await verifyPack(
      first.pack,
      verifyOptions(first.publicKey),
    );
    const recordOne = await activatePack(storage, verifiedFirst, "fa");
    const second = await makeFixture();
    const verifiedSecond = await verifyPack(
      second.pack,
      verifyOptions(second.publicKey),
    );
    await activatePack(
      storage,
      {
        ...verifiedSecond,
        manifest: { ...verifiedSecond.manifest, pack_version: "2.0.0" },
      },
      "fa",
    );
    expect((await storage.getPrevious("fa"))?.packVersion).toBe(
      recordOne.packVersion,
    );
    expect(await storage.rollback("fa")).toBe(true);
    expect((await storage.getActive("fa"))?.packVersion).toBe("1.0.0");
  });

  it("recovers from a corrupted active record", async () => {
    const storage = new MemoryPackStorage();
    const fixture = await makeFixture();
    const verified = await verifyPack(
      fixture.pack,
      verifyOptions(fixture.publicKey),
    );
    await activatePack(storage, verified, "fa");
    const active = await storage.getActive("fa");
    expect(active && (await verifyStoredRecord(active))).toBe(true);
    if (active) {
      await storage.activate({ ...active, contentHash: "0".repeat(64) });
      expect(await recoverPack(storage, "fa")).toBeUndefined();
      expect(await storage.getMeta("state.fa")).toBe("DISABLED");
    }
  });

  it("uses English fallback when no pack is installed", async () => {
    const storage = new MemoryPackStorage();
    const resolution = await resolveOffline("ckb", storage, "ar");
    expect(resolution.selected).toBe("en");
    expect(resolution.reason).toBe("mandatory_fallback");
  });
});

describe("GULS download policy", () => {
  it("blocks metered downloads under data saver", async () => {
    await expect(
      checkTransferPolicy(
        {
          dataSaverEnabled: true,
          allowMeteredNetwork: false,
          roaming: false,
          allowRoaming: false,
        },
        100,
        { onLine: true, connection: { type: "cellular" } },
      ),
    ).rejects.toMatchObject({ code: "GULS_NETWORK_METERED" });
  });

  it("resumes from a stored range and cancels cleanly", async () => {
    const storage = new MemoryPackStorage();
    const full = new Uint8Array([1, 2, 3, 4, 5, 6]);
    const progress: StagingRecord[] = [];
    let range: string | null = null;
    const fakeFetch = (async (
      _url: string,
      init: { headers: Record<string, string> },
    ) => {
      range = init.headers.Range ?? null;
      const bytes = range ? full.slice(3) : full;
      return {
        status: range ? 206 : 200,
        ok: true,
        arrayBuffer: async () => bytes.buffer,
      } as Response;
    }) as typeof fetch;
    const controller = downloadPack({
      url: "https://example.test/pack",
      token: "token",
      languageId: "fa",
      expectedSize: 6,
      expectedHash: "hash",
      policy: {
        dataSaverEnabled: false,
        allowMeteredNetwork: true,
        roaming: false,
        allowRoaming: false,
      },
      storage,
      fetchImpl: fakeFetch,
      capabilities: { onLine: true },
      onProgress: (record) => progress.push(record),
    });
    expect(Array.from(await controller.promise)).toEqual([1, 2, 3, 4, 5, 6]);
    expect(progress).toHaveLength(1);

    const cancelled = downloadPack({
      url: "https://example.test/pack",
      token: "token",
      languageId: "fa",
      expectedSize: 6,
      expectedHash: "hash2",
      policy: {
        dataSaverEnabled: false,
        allowMeteredNetwork: true,
        roaming: false,
        allowRoaming: false,
      },
      storage,
      fetchImpl: (async () => {
        await new Promise<void>(() => undefined);
        return {} as Response;
      }) as typeof fetch,
      capabilities: { onLine: true },
    });
    cancelled.cancel();
    await expect(cancelled.promise).rejects.toBeInstanceOf(GulsFailure);
  });
});
