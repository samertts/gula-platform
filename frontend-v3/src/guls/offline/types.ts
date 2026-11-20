/** Stable codes emitted by the offline language runtime. Never translated. */
export type GulsOfflineCode =
  | "GULS_PACK_UNSUPPORTED"
  | "GULS_PACK_INVALID_ARCHIVE"
  | "GULS_PACK_UNSAFE_PATH"
  | "GULS_PACK_FILE_TYPE_FORBIDDEN"
  | "GULS_PACK_TOO_LARGE"
  | "GULS_PACK_MANIFEST_INVALID"
  | "GULS_PACK_HASH_MISMATCH"
  | "GULS_PACK_SIGNATURE_INVALID"
  | "GULS_PACK_POLICY_REJECTED"
  | "GULS_PACK_INCOMPATIBLE"
  | "GULS_STORAGE_QUOTA_EXCEEDED"
  | "GULS_NETWORK_UNAVAILABLE"
  | "GULS_NETWORK_METERED"
  | "GULS_DOWNLOAD_CANCELLED"
  | "GULS_DOWNLOAD_INCOMPLETE";

export interface GulsOfflineError {
  code: GulsOfflineCode;
  parameters: Record<string, string | number>;
}

export class GulsFailure extends Error {
  readonly code: GulsOfflineCode;
  readonly parameters: Record<string, string | number>;

  constructor(
    code: GulsOfflineCode,
    parameters: Record<string, string | number> = {},
  ) {
    super(code);
    this.name = "GulsFailure";
    this.code = code;
    this.parameters = parameters;
  }

  toStableMessage(): GulsOfflineError {
    return { code: this.code, parameters: this.parameters };
  }
}

export interface PackFileEntry {
  path: string;
  sha256: string;
  size: number;
}

export interface PackManifest {
  schema_version: "1.0";
  language_id: string;
  locale_tag: string;
  native_name: string;
  fallback_locale: "en";
  pack_version: string;
  minimum_engine_version: string;
  direction: "rtl" | "ltr";
  script: string;
  catalogs: string[];
  terminology_version: string;
  content_hash: string;
  content_size: number;
  publisher: string;
  signer_key_id: string;
  approval_status: "approved" | "synthetic_test_only";
  created_at: string;
  files: PackFileEntry[];
  signature: string;
}

export interface InstalledPackRecord {
  languageId: string;
  packVersion: string;
  contentHash: string;
  manifest: PackManifest;
  files: Record<string, Uint8Array>;
  installedAt: string;
}

export interface StagingRecord {
  downloadId: string;
  languageId: string;
  expectedHash: string | null;
  expectedSize: number;
  chunks: Uint8Array[];
  receivedBytes: number;
  updatedAt: string;
}

export type PackLifecycleState =
  | "NOT_INSTALLED"
  | "AVAILABLE"
  | "QUEUED"
  | "DOWNLOADING"
  | "VERIFYING"
  | "INSTALLING"
  | "READY"
  | "UPDATE_AVAILABLE"
  | "FAILED"
  | "ROLLBACK_REQUIRED"
  | "DISABLED";

export interface StorageStatus {
  persistent: boolean;
  quotaBytes: number | null;
  usageBytes: number | null;
}

export interface StorageDriver {
  getActive(languageId: string): Promise<InstalledPackRecord | undefined>;
  getPrevious(languageId: string): Promise<InstalledPackRecord | undefined>;
  listReady(): Promise<string[]>;
  getStaging(downloadId: string): Promise<StagingRecord | undefined>;
  putStaging(record: StagingRecord): Promise<void>;
  deleteStaging(downloadId: string): Promise<void>;
  getMeta(key: string): Promise<string | undefined>;
  setMeta(key: string, value: string): Promise<void>;
  activate(record: InstalledPackRecord): Promise<void>;
  rollback(languageId: string): Promise<boolean>;
  disable(languageId: string): Promise<void>;
}
