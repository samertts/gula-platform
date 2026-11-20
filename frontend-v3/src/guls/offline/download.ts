import { GulsFailure, type StagingRecord, type StorageDriver } from "./types";

const RETRY_DELAYS_MS = [500, 1000, 2000] as const;

interface NetworkInformation {
  saveData?: boolean;
  type?: string;
  roaming?: boolean;
  effectiveType?: string;
}

interface BrowserCapabilities {
  onLine: boolean;
  connection?: NetworkInformation;
  storage?: { estimate(): Promise<{ quota?: number; usage?: number }> };
}

export interface DownloadPolicy {
  dataSaverEnabled: boolean;
  allowMeteredNetwork: boolean;
  roaming: boolean;
  allowRoaming: boolean;
}

export interface DownloadOptions {
  url: string;
  token: string;
  languageId: string;
  expectedSize: number;
  expectedHash: string | null;
  policy: DownloadPolicy;
  storage: StorageDriver;
  fetchImpl?: typeof fetch;
  capabilities?: BrowserCapabilities;
  onProgress?: (record: StagingRecord) => void;
  retryDelaysMs?: readonly number[];
}

export interface DownloadController {
  promise: Promise<Uint8Array>;
  cancel(): void;
}

function browserCapabilities(): BrowserCapabilities {
  const nav = navigator as Navigator & {
    connection?: NetworkInformation;
    storage?: BrowserCapabilities["storage"];
  };
  return {
    onLine: nav.onLine,
    connection: nav.connection,
    storage: nav.storage,
  };
}

export async function checkTransferPolicy(
  policy: DownloadPolicy,
  requiredBytes: number,
  capabilities: BrowserCapabilities,
): Promise<void> {
  if (capabilities.onLine === false)
    throw new GulsFailure("GULS_NETWORK_UNAVAILABLE");
  const connection = capabilities.connection;
  const slow =
    connection?.effectiveType === "2g" ||
    connection?.effectiveType === "slow-2g";
  const metered = Boolean(
    connection?.saveData || connection?.type === "cellular" || slow,
  );
  if (policy.dataSaverEnabled && !policy.allowMeteredNetwork && metered) {
    throw new GulsFailure("GULS_NETWORK_METERED", { reason: "data_saver" });
  }
  if (connection?.type === "cellular" && !policy.allowMeteredNetwork) {
    throw new GulsFailure("GULS_NETWORK_METERED", { reason: "cellular" });
  }
  if (policy.roaming && connection?.roaming && !policy.allowRoaming) {
    throw new GulsFailure("GULS_NETWORK_METERED", { reason: "roaming" });
  }
  if (requiredBytes > 0 && capabilities.storage) {
    // Quota is checked conservatively; the runtime needs room for the new pack
    // and the previous version kept for rollback.
    const estimate = await capabilities.storage.estimate();
    const quota = estimate.quota ?? 0;
    const usage = estimate.usage ?? 0;
    if (quota > 0 && quota - usage < requiredBytes * 2) {
      throw new GulsFailure("GULS_STORAGE_QUOTA_EXCEEDED", {
        required: requiredBytes * 2,
      });
    }
  }
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, milliseconds);
    if (typeof timer === "object" && "unref" in timer)
      (timer as { unref(): void }).unref();
  });
}

function concatenate(chunks: Uint8Array[], total: number): Uint8Array {
  const result = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.length;
  }
  return result;
}

/** Start a resumable, cancellable, policy-checked pack download. */
export function downloadPack(options: DownloadOptions): DownloadController {
  const controller = new AbortController();
  const retryDelays = options.retryDelaysMs ?? RETRY_DELAYS_MS;
  const fetchImpl = options.fetchImpl ?? fetch;
  const capabilities = options.capabilities ?? browserCapabilities();
  let cancelled = false;
  // Some fetch implementations ignore AbortSignal. Race every await against an
  // explicit cancellation promise so cancel() can never leave a hung download.
  const aborted = new Promise<never>((_resolve, reject) => {
    controller.signal.addEventListener(
      "abort",
      () => reject(new GulsFailure("GULS_DOWNLOAD_CANCELLED")),
      { once: true },
    );
  });
  void aborted.catch(() => undefined);
  const raceWithAbort = <T>(work: Promise<T>): Promise<T> =>
    Promise.race([work, aborted]);

  const promise = (async (): Promise<Uint8Array> => {
    await raceWithAbort(
      checkTransferPolicy(options.policy, options.expectedSize, capabilities),
    );
    const downloadId = `web-${options.languageId}-${options.expectedHash ?? "unhashed"}`;
    let staging = (await raceWithAbort(
      options.storage.getStaging(downloadId),
    )) ?? {
      downloadId,
      languageId: options.languageId,
      expectedHash: options.expectedHash,
      expectedSize: options.expectedSize,
      chunks: [],
      receivedBytes: 0,
      updatedAt: new Date().toISOString(),
    };
    if (
      staging.expectedHash !== options.expectedHash ||
      staging.expectedSize !== options.expectedSize
    ) {
      staging = { ...staging, chunks: [], receivedBytes: 0 };
    }

    let lastError: unknown;
    for (let attempt = 0; attempt <= retryDelays.length; attempt += 1) {
      try {
        const headers: Record<string, string> = {
          Authorization: `Bearer ${options.token}`,
        };
        if (staging.receivedBytes > 0)
          headers.Range = `bytes=${staging.receivedBytes}-`;
        const response = await raceWithAbort(
          fetchImpl(options.url, {
            headers,
            signal: controller.signal,
            cache: "no-store",
          }),
        );
        if (response.status === 429 || response.status >= 500) {
          throw new Error(`retryable_status_${response.status}`);
        }
        if (!response.ok) {
          throw new GulsFailure("GULS_DOWNLOAD_INCOMPLETE", {
            status: response.status,
          });
        }
        const chunk = new Uint8Array(
          await raceWithAbort(response.arrayBuffer()),
        );
        staging =
          response.status === 200 && staging.receivedBytes > 0
            ? { ...staging, chunks: [chunk], receivedBytes: chunk.length }
            : {
                ...staging,
                chunks: [...staging.chunks, chunk],
                receivedBytes: staging.receivedBytes + chunk.length,
              };
        staging.updatedAt = new Date().toISOString();
        await raceWithAbort(options.storage.putStaging(staging));
        options.onProgress?.(staging);

        const payload = concatenate(staging.chunks, staging.receivedBytes);
        if (options.expectedSize > 0 && payload.length < options.expectedSize) {
          throw new GulsFailure("GULS_DOWNLOAD_INCOMPLETE", {
            received: payload.length,
            expected: options.expectedSize,
          });
        }
        await raceWithAbort(options.storage.deleteStaging(downloadId));
        return payload;
      } catch (error) {
        if (cancelled || controller.signal.aborted)
          throw new GulsFailure("GULS_DOWNLOAD_CANCELLED");
        lastError = error;
        if (
          error instanceof GulsFailure &&
          error.code !== "GULS_DOWNLOAD_INCOMPLETE"
        )
          throw error;
        const retryable =
          error instanceof GulsFailure
            ? error.code === "GULS_DOWNLOAD_INCOMPLETE"
            : true;
        if (!retryable || attempt === retryDelays.length) break;
        await raceWithAbort(delay(retryDelays[attempt] ?? 0));
      }
    }
    throw lastError instanceof GulsFailure
      ? lastError
      : new GulsFailure("GULS_DOWNLOAD_INCOMPLETE", {
          reason: "retries_exhausted",
        });
  })();

  return {
    promise,
    cancel(): void {
      cancelled = true;
      controller.abort(new GulsFailure("GULS_DOWNLOAD_CANCELLED"));
    },
  };
}
