import {
  UpdateStatus,
  UpdateChannel,
  UpdateEventMap,
  UpdateEventListener,
  UpdatePackage,
  UpdateCheckResult,
  DownloadProgress,
  InstallProgress,
  UpdateError,
  UpdateErrorCode,
  UpdateState,
  ScheduledUpdate,
  UpdateScheduleConfig,
  AppIdentification,
  PlatformType,
} from '../types.js';
import { VersionManager } from './VersionManager.js';
import { UpdateScheduler } from './UpdateScheduler.js';
import { UpdateValidator } from './UpdateValidator.js';
import { PackageSigner } from '../platform/PackageSigner.js';
import { ReleaseManager } from '../platform/ReleaseManager.js';

export class UpdateManager {
  private readonly app: AppIdentification;
  private readonly versionManager: VersionManager;
  private readonly scheduler: UpdateScheduler;
  private readonly validator: UpdateValidator;
  private readonly packageSigner: PackageSigner;
  private readonly releaseManager: ReleaseManager;

  private status: UpdateStatus = UpdateStatus.Idle;
  private currentVersion: string | null = null;
  private pendingUpdate: UpdatePackage | null = null;
  private downloadProgress: DownloadProgress | null = null;
  private installProgress: InstallProgress | null = null;
  private lastCheckResult: UpdateCheckResult | null = null;
  private lastError: UpdateError | null = null;
  private scheduledUpdates: ScheduledUpdate[] = [];
  private versionHistory: string[] = [];

  private listeners: Map<string, Set<Function>> = new Map();
  private abortController: AbortController | null = null;
  private updateCheckEndpoint: string;
  private updateDownloadEndpoint: string;

  constructor(
    app: AppIdentification,
    options: {
      updateCheckEndpoint?: string;
      updateDownloadEndpoint?: string;
      scheduleConfig?: Partial<UpdateScheduleConfig>;
    } = {},
  ) {
    this.app = app;
    this.currentVersion = app.version;
    this.versionManager = new VersionManager(app.name, app.version, app.platform, app.channel);
    this.packageSigner = new PackageSigner();
    this.releaseManager = new ReleaseManager();
    this.validator = new UpdateValidator(this.versionManager, this.packageSigner);

    this.updateCheckEndpoint = options.updateCheckEndpoint || '/api/updates/check';
    this.updateDownloadEndpoint = options.updateDownloadEndpoint || '/api/updates/download';

    this.scheduler = new UpdateScheduler({
      checkInterval: 3600000,
      backgroundDownload: true,
      autoInstall: false,
      maintenanceWindow: null,
      bandwidthLimit: null,
      offlineMode: 'delay',
      maxRetries: 3,
      retryDelay: 60000,
      ...options.scheduleConfig,
    });

    this.setupSchedulerListeners();
  }

  private setupSchedulerListeners(): void {
    this.scheduler.on('check:due', async () => {
      await this.checkForUpdates(false);
    });

    this.scheduler.on('update:due', async (scheduledUpdate: ScheduledUpdate) => {
      await this.processScheduledUpdate(scheduledUpdate);
    });

    this.scheduler.on('maintenance:start', () => {
      if (this.pendingUpdate && this.status === UpdateStatus.Downloaded) {
        this.installUpdate();
      }
    });
  }

  on<K extends keyof UpdateEventMap>(
    event: K,
    listener: UpdateEventListener<K>,
  ): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener as Function);
    return () => {
      this.listeners.get(event)?.delete(listener as Function);
    };
  }

  private emit<K extends keyof UpdateEventMap>(event: K, data: UpdateEventMap[K]): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }

  private setStatus(newStatus: UpdateStatus): void {
    const oldStatus = this.status;
    this.status = newStatus;
    this.emit('status:change', { from: oldStatus, to: newStatus });
  }

  getState(): UpdateState {
    return {
      status: this.status,
      currentVersion: this.currentVersion,
      pendingUpdate: this.pendingUpdate,
      downloadProgress: this.downloadProgress,
      installProgress: this.installProgress,
      lastCheckResult: this.lastCheckResult,
      lastError: this.lastError,
      scheduledUpdates: [...this.scheduledUpdates],
      checkInterval: this.scheduler.getConfig().checkInterval,
      maintenanceWindow: this.scheduler.getConfig().maintenanceWindow || null,
      channel: this.app.channel,
    };
  }

  async checkForUpdates(manual: boolean = false): Promise<UpdateCheckResult> {
    this.emit('check:start', { manual });
    this.setStatus(UpdateStatus.Checking);
    this.lastError = null;

    try {
      const response = await fetch(this.updateCheckEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appName: this.app.name,
          currentVersion: this.app.version,
          buildNumber: this.app.buildNumber,
          platform: this.app.platform,
          channel: this.app.channel,
        }),
      });

      if (!response.ok) {
        throw new Error(`Update check failed: ${response.status} ${response.statusText}`);
      }

      const result: UpdateCheckResult = await response.json();

      this.lastCheckResult = result;
      this.scheduler.markCheckDone();

      if (result.available && result.package) {
        this.pendingUpdate = result.package;
        this.setStatus(UpdateStatus.Available);

        if (result.forced) {
          await this.downloadUpdate();
        }
      } else {
        this.setStatus(UpdateStatus.Idle);
      }

      this.emit('check:complete', result);
      return result;
    } catch (error) {
      const updateError: UpdateError = {
        code: UpdateErrorCode.NetworkError,
        message: (error as Error).message,
        details: null,
        recoverable: true,
      };
      this.lastError = updateError;
      this.setStatus(UpdateStatus.Error);
      this.emit('error', updateError);
      this.scheduler.markCheckDone();

      return {
        available: false,
        currentVersion: this.currentVersion || '',
        latestVersion: null,
        package: null,
        forced: false,
        releaseNotes: [],
        error: (error as Error).message,
      };
    }
  }

  async downloadUpdate(): Promise<void> {
    if (!this.pendingUpdate) {
      throw new Error('No pending update to download');
    }

    const validationResult = await this.validator.validate(this.pendingUpdate);
    if (!validationResult.valid) {
      const error: UpdateError = {
        code: UpdateErrorCode.ValidationFailed,
        message: 'Update validation failed',
        details: validationResult.errors.map((e) => e.message).join('; '),
        recoverable: false,
      };
      this.lastError = error;
      this.setStatus(UpdateStatus.Error);
      this.emit('error', error);
      return;
    }

    this.abortController = new AbortController();
    this.setStatus(UpdateStatus.Downloading);
    this.emit('download:start', this.pendingUpdate);

    try {
      const downloadUrl = `${this.updateDownloadEndpoint}/${this.pendingUpdate.id}`;

      const preCheckResult = await this.validator.runPreUpdateChecks();
      if (!preCheckResult.passed) {
        throw new Error(`Pre-update checks failed: ${preCheckResult.errors.join(', ')}`);
      }

      const response = await fetch(downloadUrl, {
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status} ${response.statusText}`);
      }

      const contentLength = response.headers.get('content-length');
      const totalBytes = contentLength ? parseInt(contentLength, 10) : this.pendingUpdate.size;
      const reader = response.body!.getReader();
      let bytesDownloaded = 0;
      const startTime = Date.now();

      const chunks: Uint8Array[] = [];
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        chunks.push(value);
        bytesDownloaded += value.length;
        const elapsedSeconds = (Date.now() - startTime) / 1000;
        const speed = elapsedSeconds > 0 ? bytesDownloaded / elapsedSeconds : 0;

        this.downloadProgress = {
          bytesDownloaded,
          totalBytes,
          percentage: (bytesDownloaded / totalBytes) * 100,
          speed,
          estimatedSecondsRemaining: speed > 0 ? (totalBytes - bytesDownloaded) / speed : Infinity,
        };

        this.scheduler.recordBandwidth(speed);
        this.emit('download:progress', this.downloadProgress);
      }

      if (this.abortController.signal.aborted) {
        throw new Error('Download cancelled');
      }

      const blob = new Blob(chunks);
      const checksum = await this.computeChecksum(
        blob,
        this.pendingUpdate.checksumAlgorithm,
      );

      if (checksum !== this.pendingUpdate.checksum) {
        throw new Error(
          `Checksum mismatch: expected ${this.pendingUpdate.checksum}, computed ${checksum}`,
        );
      }

      this.setStatus(UpdateStatus.Downloaded);
      this.emit('download:complete', this.pendingUpdate);

      if (this.scheduler.getConfig().autoInstall) {
        await this.installUpdate();
      }
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        this.setStatus(UpdateStatus.Available);
        return;
      }

      const updateError: UpdateError = {
        code: UpdateErrorCode.DownloadFailed,
        message: (error as Error).message,
        details: null,
        recoverable: true,
      };
      this.lastError = updateError;
      this.setStatus(UpdateStatus.Error);
      this.emit('error', updateError);
    }
  }

  async installUpdate(): Promise<void> {
    if (!this.pendingUpdate || this.status !== UpdateStatus.Downloaded) {
      throw new Error('No downloaded update to install');
    }

    this.setStatus(UpdateStatus.Installing);
    this.emit('install:start', this.pendingUpdate);
    this.lastError = null;

    try {
      const phases: InstallProgress['phase'][] = ['extracting', 'verifying', 'applying', 'cleaning'];

      for (const phase of phases) {
        this.installProgress = { phase, percentage: 0, message: `Starting ${phase}...` };
        this.emit('install:progress', this.installProgress);

        const phasePercentages: Record<string, number> = {
          extracting: 25,
          verifying: 50,
          applying: 85,
          cleaning: 100,
        };

        for (let pct = 0; pct <= phasePercentages[phase]; pct += 5) {
          this.installProgress = {
            phase,
            percentage: pct,
            message: `${phase} progress: ${pct}%`,
          };
          this.emit('install:progress', this.installProgress);
          await this.delay(50);
        }
      }

      this.versionHistory.push(this.currentVersion!);
      this.currentVersion = this.pendingUpdate.version;

      const postCheckResult = await this.validator.runPostUpdateChecks();
      if (!postCheckResult.passed) {
        console.warn('Post-update checks had issues:', postCheckResult.errors.join(', '));
      }

      this.setStatus(UpdateStatus.Installed);
      this.emit('install:complete', this.pendingUpdate);
      this.pendingUpdate = null;
      this.downloadProgress = null;
      this.installProgress = null;
    } catch (error) {
      const updateError: UpdateError = {
        code: UpdateErrorCode.InstallFailed,
        message: (error as Error).message,
        details: null,
        recoverable: true,
      };
      this.lastError = updateError;
      this.setStatus(UpdateStatus.Error);
      this.emit('install:error', updateError);
      this.emit('error', updateError);
    }
  }

  async rollback(): Promise<boolean> {
    if (this.versionHistory.length === 0) {
      this.lastError = {
        code: UpdateErrorCode.RollbackFailed,
        message: 'No previous version to rollback to',
        details: null,
        recoverable: false,
      };
      return false;
    }

    const previousVersion = this.versionHistory[this.versionHistory.length - 1];
    this.emit('rollback:start', { from: this.currentVersion || '', to: previousVersion });

    try {
      this.currentVersion = previousVersion;
      this.versionHistory.pop();

      this.setStatus(UpdateStatus.RolledBack);
      this.emit('rollback:complete', {
        from: this.currentVersion || '',
        to: previousVersion,
      });
      return true;
    } catch (error) {
      const updateError: UpdateError = {
        code: UpdateErrorCode.RollbackFailed,
        message: (error as Error).message,
        details: null,
        recoverable: false,
      };
      this.lastError = updateError;
      this.emit('rollback:error', updateError);
      return false;
    }
  }

  cancelDownload(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }

    if (this.status === UpdateStatus.Downloading) {
      this.setStatus(UpdateStatus.Available);
    }
  }

  scheduleUpdateForLater(updateId: string, scheduledTime: string): void {
    const scheduled: ScheduledUpdate = {
      id: crypto.randomUUID(),
      packageId: updateId,
      scheduledFor: scheduledTime,
      status: 'pending',
      maintenanceWindow: this.scheduler.getConfig().maintenanceWindow || null,
      retryCount: 0,
      maxRetries: this.scheduler.getConfig().maxRetries,
      lastError: null,
    };
    this.scheduler.scheduleUpdate(scheduled);
    this.scheduledUpdates.push(scheduled);
  }

  async checkForUpdatesAndNotify(): Promise<UpdateCheckResult> {
    const result = await this.checkForUpdates(false);
    if (result.available) {
      this.setStatus(UpdateStatus.Available);
    }
    return result;
  }

  getAppInfo(): AppIdentification {
    return { ...this.app };
  }

  getVersionHistory(): ReadonlyArray<string> {
    return [...this.versionHistory];
  }

  getScheduler(): UpdateScheduler {
    return this.scheduler;
  }

  getReleaseManager(): ReleaseManager {
    return this.releaseManager;
  }

  setChannel(channel: UpdateChannel): void {
    this.app.channel = channel;
  }

  private async processScheduledUpdate(scheduledUpdate: ScheduledUpdate): Promise<void> {
    try {
      scheduledUpdate.status = 'installing';
      await this.checkForUpdates(false);
    } catch (error) {
      scheduledUpdate.status = 'failed';
      scheduledUpdate.lastError = (error as Error).message;
      scheduledUpdate.retryCount++;

      if (scheduledUpdate.retryCount < scheduledUpdate.maxRetries) {
        const delay = this.scheduler.getConfig().retryDelay * Math.pow(2, scheduledUpdate.retryCount);
        setTimeout(() => {
          this.scheduler.scheduleUpdate(scheduledUpdate);
        }, delay);
      }
    }
  }

  private async computeChecksum(blob: Blob, algorithm: 'sha256' | 'sha512'): Promise<string> {
    const hashAlgo = algorithm === 'sha512' ? 'SHA-512' : 'SHA-256';
    const buffer = await blob.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest(hashAlgo, buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  destroy(): void {
    this.cancelDownload();
    this.scheduler.destroy();
    this.listeners.clear();
    this.versionHistory = [];
    this.pendingUpdate = null;
    this.scheduledUpdates = [];
    this.setStatus(UpdateStatus.Idle);
  }
}
