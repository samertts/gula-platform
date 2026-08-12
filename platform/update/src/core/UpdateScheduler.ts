import {
  UpdateScheduleConfig,
  ScheduledUpdate,
  MaintenanceWindow,
  UpdateState,
  DownloadProgress,
} from '../types.js';

interface SchedulerEventMap {
  'check:due': { scheduledTime: number };
  'update:due': ScheduledUpdate;
  'maintenance:start': MaintenanceWindow;
  'maintenance:end': MaintenanceWindow;
  'offline:detected': void;
  'online:detected': void;
}

type SchedulerEventListener<K extends keyof SchedulerEventMap> = (event: SchedulerEventMap[K]) => void;

export class UpdateScheduler {
  private config: UpdateScheduleConfig;
  private checkTimer: ReturnType<typeof setInterval> | null = null;
  private maintenanceTimer: ReturnType<typeof setTimeout> | null = null;
  private pendingUpdates: ScheduledUpdate[] = [];
  private isOnline: boolean = true;
  private lastCheckTime: number = 0;
  private nextCheckTime: number = 0;
  private listeners: Map<string, Set<Function>> = new Map();
  private bandwidthHistory: number[] = [];
  private scheduleCheckInterval: ReturnType<typeof setInterval> | null = null;

  constructor(config: UpdateScheduleConfig) {
    this.config = {
      checkInterval: 3600000,
      backgroundDownload: true,
      autoInstall: false,
      maintenanceWindow: null,
      bandwidthLimit: null,
      offlineMode: 'delay',
      maxRetries: 3,
      retryDelay: 60000,
      ...config,
    };

    if (typeof navigator !== 'undefined') {
      this.isOnline = navigator.onLine;
      window.addEventListener('online', () => {
        this.isOnline = true;
        this.emit('online:detected', undefined);
      });
      window.addEventListener('offline', () => {
        this.isOnline = false;
        this.emit('offline:detected', undefined);
      });
    }

    this.scheduleNextCheck();
  }

  on<K extends keyof SchedulerEventMap>(
    event: K,
    listener: SchedulerEventListener<K>,
  ): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener as Function);
    return () => {
      this.listeners.get(event)?.delete(listener as Function);
    };
  }

  private emit<K extends keyof SchedulerEventMap>(event: K, data: SchedulerEventMap[K]): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }

  start(): void {
    this.scheduleNextCheck();
    this.startMaintenanceWatcher();
    this.startScheduleChecker();
  }

  stop(): void {
    if (this.checkTimer) {
      clearInterval(this.checkTimer);
      this.checkTimer = null;
    }
    if (this.maintenanceTimer) {
      clearTimeout(this.maintenanceTimer);
      this.maintenanceTimer = null;
    }
    if (this.scheduleCheckInterval) {
      clearInterval(this.scheduleCheckInterval);
      this.scheduleCheckInterval = null;
    }
  }

  updateConfig(config: Partial<UpdateScheduleConfig>): void {
    this.config = { ...this.config, ...config };
    if (config.checkInterval !== undefined || config.maintenanceWindow !== undefined) {
      this.reschedule();
    }
  }

  getConfig(): Readonly<UpdateScheduleConfig> {
    return { ...this.config };
  }

  getPendingUpdates(): ReadonlyArray<ScheduledUpdate> {
    return [...this.pendingUpdates];
  }

  scheduleUpdate(update: ScheduledUpdate): void {
    const existingIndex = this.pendingUpdates.findIndex((u) => u.id === update.id);
    if (existingIndex >= 0) {
      this.pendingUpdates[existingIndex] = update;
    } else {
      this.pendingUpdates.push(update);
    }
    this.pendingUpdates.sort((a, b) => new Date(a.scheduledFor).getTime() - new Date(b.scheduledFor).getTime());
  }

  cancelScheduledUpdate(updateId: string): boolean {
    const index = this.pendingUpdates.findIndex((u) => u.id === updateId);
    if (index >= 0) {
      this.pendingUpdates[index].status = 'cancelled';
      this.pendingUpdates.splice(index, 1);
      return true;
    }
    return false;
  }

  recordBandwidth(bytesPerSecond: number): void {
    this.bandwidthHistory.push(bytesPerSecond);
    if (this.bandwidthHistory.length > 20) {
      this.bandwidthHistory.shift();
    }
  }

  getEstimatedBandwidth(): number {
    if (this.bandwidthHistory.length === 0) return Infinity;
    return this.bandwidthHistory.reduce((a, b) => a + b, 0) / this.bandwidthHistory.length;
  }

  shouldDownloadNow(packageSize: number): boolean {
    if (this.config.bandwidthLimit === null) return true;

    const estimatedBandwidth = this.getEstimatedBandwidth();
    const estimatedTime = packageSize / Math.max(estimatedBandwidth, 1);

    if (estimatedTime > 300 && this.isOffPeakHours()) {
      return false;
    }

    return estimatedBandwidth > 0;
  }

  private isOffPeakHours(): boolean {
    const hour = new Date().getHours();
    return hour >= 2 && hour <= 5;
  }

  isWithinMaintenanceWindow(): boolean {
    if (!this.config.maintenanceWindow) return true;

    const now = new Date();
    const start = new Date(this.config.maintenanceWindow.startTime);
    const end = new Date(this.config.maintenanceWindow.endTime);

    const dayOfWeek = now.getDay();
    if (!this.config.maintenanceWindow.daysOfWeek.includes(dayOfWeek)) {
      return false;
    }

    const nowMinutes = now.getHours() * 60 + now.getMinutes();
    const startMinutes = start.getHours() * 60 + start.getMinutes();
    const endMinutes = end.getHours() * 60 + end.getMinutes();

    if (startMinutes <= endMinutes) {
      return nowMinutes >= startMinutes && nowMinutes <= endMinutes;
    }
    return nowMinutes >= startMinutes || nowMinutes <= endMinutes;
  }

  isDueForCheck(): boolean {
    return Date.now() >= this.nextCheckTime;
  }

  markCheckDone(): void {
    this.lastCheckTime = Date.now();
    this.scheduleNextCheck();
  }

  private scheduleNextCheck(): void {
    const interval = this.config.checkInterval;
    let adjustedInterval = interval;

    const bandwidth = this.getEstimatedBandwidth();
    if (bandwidth < 50000 && bandwidth > 0) {
      adjustedInterval = interval * 2;
    }

    this.nextCheckTime = Date.now() + adjustedInterval;

    if (this.checkTimer) {
      clearInterval(this.checkTimer);
    }

    this.checkTimer = setInterval(() => {
      if (!this.shouldSkipCheck()) {
        this.emit('check:due', { scheduledTime: Date.now() });
      }
    }, adjustedInterval);
  }

  private shouldSkipCheck(): boolean {
    if (this.config.offlineMode === 'skip' && !this.isOnline) {
      return true;
    }
    if (this.config.offlineMode === 'delay' && !this.isOnline) {
      return false;
    }
    return false;
  }

  private reschedule(): void {
    this.scheduleNextCheck();
  }

  private startMaintenanceWatcher(): void {
    if (!this.config.maintenanceWindow) return;

    const checkMaintenance = () => {
      if (this.isWithinMaintenanceWindow()) {
        this.emit('maintenance:start', this.config.maintenanceWindow!);
      } else {
        this.emit('maintenance:end', this.config.maintenanceWindow!);
      }
    };

    checkMaintenance();
    setInterval(checkMaintenance, 60000);
  }

  private startScheduleChecker(): void {
    this.scheduleCheckInterval = setInterval(() => {
      const now = Date.now();
      for (const update of this.pendingUpdates) {
        if (
          update.status === 'pending' &&
          new Date(update.scheduledFor).getTime() <= now
        ) {
          this.emit('update:due', update);
        }
      }
    }, 10000);
  }

  getTimeUntilNextCheck(): number {
    return Math.max(0, this.nextCheckTime - Date.now());
  }

  destroy(): void {
    this.stop();
    this.listeners.clear();
    this.pendingUpdates = [];
    this.bandwidthHistory = [];
  }
}
