import {
  UpdateStatus,
  UpdatePackage,
  UpdateCheckResult,
  DownloadProgress,
  UpdateError,
  UpdateErrorCode,
  UpdateChannel,
} from '../types.js';
import { UpdateManager } from '../core/UpdateManager.js';

export interface DesktopAutoUpdaterOptions {
  autoDownload: boolean;
  autoInstallOnQuit: boolean;
  showNotification: boolean;
  checkOnStartup: boolean;
  checkInterval: number;
  allowDowngrade: boolean;
  updateServerUrl: string;
  channel: UpdateChannel;
  notifyOnBackgroundDownload: boolean;
}

export class DesktopAutoUpdater {
  private updateManager: UpdateManager;
  private options: DesktopAutoUpdaterOptions;
  private isQuitting: boolean = false;
  private backgroundDownloadComplete: boolean = false;
  private onUpdateCallbacks: Array<(info: UpdatePackage) => void> = [];
  private onErrorCallbacks: Array<(error: UpdateError) => void> = [];
  private onProgressCallbacks: Array<(progress: DownloadProgress) => void> = [];
  private onReadyCallbacks: Array<() => void> = [];
  private downloadPromise: Promise<void> | null = null;

  constructor(
    updateManager: UpdateManager,
    options: Partial<DesktopAutoUpdaterOptions> = {},
  ) {
    this.updateManager = updateManager;
    this.options = {
      autoDownload: true,
      autoInstallOnQuit: true,
      showNotification: true,
      checkOnStartup: true,
      checkInterval: 3600000,
      allowDowngrade: false,
      updateServerUrl: '',
      channel: UpdateChannel.Stable,
      notifyOnBackgroundDownload: true,
      ...options,
    };

    this.setupListeners();
  }

  private setupListeners(): void {
    this.updateManager.on('check:complete', (result: UpdateCheckResult) => {
      if (result.available && result.package) {
        this.onUpdateCallbacks.forEach((cb) => cb(result.package!));

        if (this.options.autoDownload) {
          this.downloadInBackground();
        }
      }
    });

    this.updateManager.on('download:progress', (progress: DownloadProgress) => {
      this.onProgressCallbacks.forEach((cb) => cb(progress));
    });

    this.updateManager.on('download:complete', () => {
      this.backgroundDownloadComplete = true;
      if (this.options.notifyOnBackgroundDownload) {
        this.onReadyCallbacks.forEach((cb) => cb());
      }

      if (this.isQuitting && this.options.autoInstallOnQuit) {
        this.installOnQuit();
      }
    });

    this.updateManager.on('error', (error: UpdateError) => {
      if (error.code === UpdateErrorCode.NetworkError) {
        this.scheduleRetry();
      }
      this.onErrorCallbacks.forEach((cb) => cb(error));
    });
  }

  initialize(): void {
    if (this.options.checkOnStartup) {
      setTimeout(() => {
        this.checkForUpdates();
      }, 3000);
    }

    this.startPeriodicChecks();
  }

  async checkForUpdates(): Promise<UpdateCheckResult> {
    return this.updateManager.checkForUpdates(true);
  }

  async downloadInBackground(): Promise<void> {
    if (this.downloadPromise) return this.downloadPromise;

    this.downloadPromise = this.updateManager.downloadUpdate().finally(() => {
      this.downloadPromise = null;
    });

    return this.downloadPromise;
  }

  async installOnQuit(): Promise<void> {
    this.isQuitting = true;

    if (!this.backgroundDownloadComplete) {
      return;
    }

    await this.updateManager.installUpdate();
  }

  quitAndInstall(): void {
    this.isQuitting = true;

    if (this.backgroundDownloadComplete) {
      this.updateManager.installUpdate().then(() => {
        this.restartApp();
      });
    } else {
      this.downloadInBackground().then(() => {
        this.updateManager.installUpdate().then(() => {
          this.restartApp();
        });
      });
    }
  }

  onUpdate(callback: (info: UpdatePackage) => void): () => void {
    this.onUpdateCallbacks.push(callback);
    return () => {
      this.onUpdateCallbacks = this.onUpdateCallbacks.filter((cb) => cb !== callback);
    };
  }

  onError(callback: (error: UpdateError) => void): () => void {
    this.onErrorCallbacks.push(callback);
    return () => {
      this.onErrorCallbacks = this.onErrorCallbacks.filter((cb) => cb !== callback);
    };
  }

  onProgress(callback: (progress: DownloadProgress) => void): () => void {
    this.onProgressCallbacks.push(callback);
    return () => {
      this.onProgressCallbacks = this.onProgressCallbacks.filter((cb) => cb !== callback);
    };
  }

  onReady(callback: () => void): () => void {
    this.onReadyCallbacks.push(callback);
    return () => {
      this.onReadyCallbacks = this.onReadyCallbacks.filter((cb) => cb !== callback);
    };
  }

  getDownloadedVersion(): string | null {
    const state = this.updateManager.getState();
    if (state.status === UpdateStatus.Downloaded && state.pendingUpdate) {
      return state.pendingUpdate.version;
    }
    return null;
  }

  isUpdateAvailable(): boolean {
    const state = this.updateManager.getState();
    return (
      state.status === UpdateStatus.Available ||
      state.status === UpdateStatus.Downloading ||
      state.status === UpdateStatus.Downloaded
    );
  }

  setFeedURL(url: string): void {
    this.options.updateServerUrl = url;
  }

  setChannel(channel: UpdateChannel): void {
    this.options.channel = channel;
    this.updateManager.setChannel(channel);
  }

  private startPeriodicChecks(): void {
    setInterval(() => {
      this.checkForUpdates();
    }, this.options.checkInterval);
  }

  private scheduleRetry(): void {
    setTimeout(() => {
      this.checkForUpdates();
    }, 60000);
  }

  private restartApp(): void {
    if (typeof window !== 'undefined' && 'electronAPI' in window) {
      (window as any).electronAPI.restartApp();
    } else if (typeof process !== 'undefined' && process.env.ELECTRON_RUN_AS_NODE) {
      process.exit(0);
    }
  }
}
