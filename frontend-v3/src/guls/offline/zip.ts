import { GulsFailure } from "./types";

const MAX_PACK_FILE_BYTES = 10 * 1024 * 1024;
const MAX_PACK_TOTAL_BYTES = 50 * 1024 * 1024;
const MAX_PACK_MEMBERS = 256;
const ALLOWED_SUFFIXES = new Set([
  ".json",
  ".md",
  ".txt",
  ".woff",
  ".woff2",
  ".ttf",
  ".otf",
]);
const FORBIDDEN_SUFFIXES = new Set([
  ".exe",
  ".dll",
  ".so",
  ".dylib",
  ".js",
  ".mjs",
  ".cjs",
  ".py",
  ".pyc",
  ".sh",
  ".bash",
  ".bat",
  ".cmd",
  ".ps1",
  ".apk",
  ".ipa",
  ".dmg",
  ".jar",
]);
const EOCD = 0x06054b50;
const CENTRAL = 0x02014b50;
const LOCAL = 0x04034b50;

interface CentralEntry {
  name: string;
  method: number;
  compressedSize: number;
  uncompressedSize: number;
  externalAttributes: number;
  localOffset: number;
}

function u16(view: DataView, offset: number): number {
  return view.getUint16(offset, true);
}

function u32(view: DataView, offset: number): number {
  return view.getUint32(offset, true);
}

function findEndOfCentralDirectory(bytes: Uint8Array): number {
  if (bytes.length < 22) {
    throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
      reason: "archive_too_short",
    });
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const minimum = Math.max(0, bytes.length - 65557);
  for (let offset = bytes.length - 22; offset >= minimum; offset -= 1) {
    if (u32(view, offset) === EOCD) return offset;
  }
  throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
    reason: "end_of_central_directory_missing",
  });
}

function readCentralDirectory(bytes: Uint8Array): CentralEntry[] {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const eocd = findEndOfCentralDirectory(bytes);
  const count = u16(view, eocd + 10);
  const directoryOffset = u32(view, eocd + 16);
  const entries: CentralEntry[] = [];
  let cursor = directoryOffset;
  for (let index = 0; index < count; index += 1) {
    if (cursor + 46 > bytes.length || u32(view, cursor) !== CENTRAL) {
      throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
        reason: "central_directory_corrupt",
      });
    }
    const nameLength = u16(view, cursor + 28);
    const extraLength = u16(view, cursor + 30);
    const commentLength = u16(view, cursor + 32);
    const nameStart = cursor + 46;
    if (nameStart + nameLength + extraLength + commentLength > bytes.length) {
      throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
        reason: "central_entry_truncated",
      });
    }
    const name = new TextDecoder().decode(
      bytes.subarray(nameStart, nameStart + nameLength),
    );
    entries.push({
      name,
      method: u16(view, cursor + 10),
      compressedSize: u32(view, cursor + 20),
      uncompressedSize: u32(view, cursor + 24),
      externalAttributes: u32(view, cursor + 38),
      localOffset: u32(view, cursor + 42),
    });
    cursor = nameStart + nameLength + extraLength + commentLength;
  }
  return entries;
}

function assertSafePath(path: string): void {
  if (
    !path ||
    path.startsWith("/") ||
    path.includes("\\") ||
    path.includes("\0") ||
    path.includes(":")
  ) {
    throw new GulsFailure("GULS_PACK_UNSAFE_PATH", { path });
  }
  const segments = path.split("/");
  if (
    segments.some(
      (segment) => segment === ".." || segment === "." || segment === "",
    )
  ) {
    throw new GulsFailure("GULS_PACK_UNSAFE_PATH", { path });
  }
  const name = segments[segments.length - 1] ?? "";
  const dot = name.lastIndexOf(".");
  const suffix = dot >= 0 ? name.slice(dot).toLowerCase() : "";
  if (
    FORBIDDEN_SUFFIXES.has(suffix) ||
    (name !== "manifest.json" && !ALLOWED_SUFFIXES.has(suffix))
  ) {
    throw new GulsFailure("GULS_PACK_FILE_TYPE_FORBIDDEN", { path });
  }
}

async function inflate(bytes: Uint8Array): Promise<Uint8Array> {
  if (typeof DecompressionStream === "undefined") {
    throw new GulsFailure("GULS_PACK_UNSUPPORTED", {
      reason: "decompression_stream_unavailable",
    });
  }
  const stream = new Blob([bytes as BlobPart])
    .stream()
    .pipeThrough(new DecompressionStream("deflate-raw"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/** Extract a data-only language pack with the same safety rules as the backend. */
export async function extractPackArchive(
  packBytes: Uint8Array,
): Promise<Record<string, Uint8Array>> {
  const entries = readCentralDirectory(packBytes);
  if (entries.length > MAX_PACK_MEMBERS) {
    throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
      reason: "too_many_members",
      count: entries.length,
    });
  }
  const view = new DataView(
    packBytes.buffer,
    packBytes.byteOffset,
    packBytes.byteLength,
  );
  const files: Record<string, Uint8Array> = {};
  let total = 0;
  for (const entry of entries) {
    assertSafePath(entry.name);
    if (
      entry.compressedSize > MAX_PACK_FILE_BYTES ||
      entry.uncompressedSize > MAX_PACK_FILE_BYTES
    ) {
      throw new GulsFailure("GULS_PACK_TOO_LARGE", {
        path: entry.name,
        size: entry.uncompressedSize,
      });
    }
    total += entry.uncompressedSize;
    if (total > MAX_PACK_TOTAL_BYTES)
      throw new GulsFailure("GULS_PACK_TOO_LARGE", { reason: "archive_total" });
    const mode = (entry.externalAttributes >>> 16) & 0o170000;
    if (mode === 0o120000)
      throw new GulsFailure("GULS_PACK_UNSAFE_PATH", {
        reason: "symlink",
        path: entry.name,
      });
    if (
      entry.localOffset + 30 > packBytes.length ||
      u32(view, entry.localOffset) !== LOCAL
    ) {
      throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
        reason: "local_header_corrupt",
        path: entry.name,
      });
    }
    const nameLength = u16(view, entry.localOffset + 26);
    const extraLength = u16(view, entry.localOffset + 28);
    const start = entry.localOffset + 30 + nameLength + extraLength;
    const end = start + entry.compressedSize;
    if (end > packBytes.length)
      throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
        reason: "payload_truncated",
        path: entry.name,
      });
    const payload = packBytes.subarray(start, end);
    let content: Uint8Array;
    if (entry.method === 0) {
      content = payload;
    } else if (entry.method === 8) {
      content = await inflate(payload);
    } else {
      throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
        reason: "unsupported_compression",
        method: entry.method,
      });
    }
    if (content.length !== entry.uncompressedSize) {
      throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
        reason: "size_mismatch",
        path: entry.name,
      });
    }
    if (files[entry.name]) {
      throw new GulsFailure("GULS_PACK_INVALID_ARCHIVE", {
        reason: "duplicate_member",
        path: entry.name,
      });
    }
    files[entry.name] = content;
  }
  return files;
}
