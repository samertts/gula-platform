import { UpdateChannel, UpdatePackage, ReleaseNotes, UpdatePriority } from '../types.js';

export interface Release {
  id: string;
  appName: string;
  version: string;
  buildNumber: string;
  channel: UpdateChannel;
  status: ReleaseStatus;
  notes: ReleaseNotes;
  package: UpdatePackage;
  artifactUrl: string;
  createdAt: string;
  publishedAt: string | null;
  rollbackTo: string | null;
  canaryPercentage: number;
  stagedRolloutPercentage: number;
  stagedRolloutGroups: string[];
  isBlueGreen: boolean;
  activeDeployment: 'blue' | 'green';
}

export enum ReleaseStatus {
  Draft = 'draft',
  Testing = 'testing',
  Staged = 'staged',
  Published = 'published',
  RolledBack = 'rolledBack',
  Archived = 'archived',
  Failed = 'failed',
}

export interface StagedRolloutConfig {
  enabled: boolean;
  initialPercentage: number;
  increment: number;
  interval: number;
  maxPercentage: number;
  groups: string[];
}

export class ReleaseManager {
  private releases: Map<string, Release> = new Map();
  private currentDeployment: 'blue' | 'green' = 'blue';
  private stagedRollouts: Map<string, StagedRolloutConfig> = new Map();
  private rollbackHistory: Map<string, string[]> = new Map();

  async createRelease(params: {
    appName: string;
    version: string;
    buildNumber: string;
    channel: UpdateChannel;
    notes: Omit<ReleaseNotes, 'date'>;
    package: UpdatePackage;
    artifactUrl: string;
    canaryPercentage?: number;
    stagedRolloutPercentage?: number;
  }): Promise<Release> {
    const release: Release = {
      id: crypto.randomUUID(),
      appName: params.appName,
      version: params.version,
      buildNumber: params.buildNumber,
      channel: params.channel,
      status: ReleaseStatus.Draft,
      notes: {
        ...params.notes,
        date: new Date().toISOString(),
      },
      package: params.package,
      artifactUrl: params.artifactUrl,
      createdAt: new Date().toISOString(),
      publishedAt: null,
      rollbackTo: null,
      canaryPercentage: params.canaryPercentage || 0,
      stagedRolloutPercentage: params.stagedRolloutPercentage || 100,
      stagedRolloutGroups: [],
      isBlueGreen: false,
      activeDeployment: 'blue',
    };

    this.releases.set(release.id, release);
    if (!this.rollbackHistory.has(params.appName)) {
      this.rollbackHistory.set(params.appName, []);
    }
    this.rollbackHistory.get(params.appName)!.push(release.id);

    return release;
  }

  async publishRelease(releaseId: string): Promise<Release> {
    const release = this.releases.get(releaseId);
    if (!release) {
      throw new Error(`Release not found: ${releaseId}`);
    }

    release.status = ReleaseStatus.Published;
    release.publishedAt = new Date().toISOString();

    if (release.canaryPercentage > 0) {
      release.status = ReleaseStatus.Staged;
    }

    this.releases.set(releaseId, release);
    return release;
  }

  async rollbackRelease(releaseId: string): Promise<Release> {
    const release = this.releases.get(releaseId);
    if (!release) {
      throw new Error(`Release not found: ${releaseId}`);
    }

    const history = this.rollbackHistory.get(release.appName) || [];
    const previousIndex = history.indexOf(releaseId) - 1;
    const previousReleaseId = previousIndex >= 0 ? history[previousIndex] : null;

    release.status = ReleaseStatus.RolledBack;
    release.rollbackTo = previousReleaseId;

    if (previousReleaseId) {
      const previousRelease = this.releases.get(previousReleaseId);
      if (previousRelease) {
        previousRelease.status = ReleaseStatus.Published;
        previousRelease.publishedAt = new Date().toISOString();
        this.releases.set(previousReleaseId, previousRelease);
      }
    }

    this.releases.set(releaseId, release);
    return release;
  }

  async setupBlueGreenDeployment(
    releaseId: string,
    initialDeployment: 'blue' | 'green' = 'green',
  ): Promise<Release> {
    const release = this.releases.get(releaseId);
    if (!release) {
      throw new Error(`Release not found: ${releaseId}`);
    }

    release.isBlueGreen = true;
    release.activeDeployment = initialDeployment;
    release.status = ReleaseStatus.Staged;
    this.releases.set(releaseId, release);

    return release;
  }

  switchBlueGreenDeployment(releaseId: string): Release {
    const release = this.releases.get(releaseId);
    if (!release) {
      throw new Error(`Release not found: ${releaseId}`);
    }

    release.activeDeployment = release.activeDeployment === 'blue' ? 'green' : 'blue';
    this.currentDeployment = release.activeDeployment;
    this.releases.set(releaseId, release);

    return release;
  }

  async setupStagedRollout(
    releaseId: string,
    config: StagedRolloutConfig,
  ): Promise<void> {
    const release = this.releases.get(releaseId);
    if (!release) {
      throw new Error(`Release not found: ${releaseId}`);
    }

    this.stagedRollouts.set(releaseId, config);
    release.status = ReleaseStatus.Staged;
    release.stagedRolloutPercentage = config.initialPercentage;
    release.stagedRolloutGroups = config.groups;
    this.releases.set(releaseId, release);

    if (config.enabled && config.interval > 0) {
      this.startStagedRolloutTimer(releaseId, config);
    }
  }

  private startStagedRolloutTimer(releaseId: string, config: StagedRolloutConfig): void {
    const timer = setInterval(() => {
      const release = this.releases.get(releaseId);
      if (!release || release.status !== ReleaseStatus.Staged) {
        clearInterval(timer);
        return;
      }

      const newPercentage = Math.min(
        release.stagedRolloutPercentage + config.increment,
        config.maxPercentage,
      );

      release.stagedRolloutPercentage = newPercentage;
      this.releases.set(releaseId, release);

      if (newPercentage >= config.maxPercentage) {
        release.status = ReleaseStatus.Published;
        this.releases.set(releaseId, release);
        clearInterval(timer);
      }
    }, config.interval);
  }

  getLatestRelease(
    appName: string,
    channel: UpdateChannel,
  ): Release | null {
    const releases = Array.from(this.releases.values())
      .filter((r) => r.appName === appName && r.channel === channel)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    for (const release of releases) {
      if (release.status === ReleaseStatus.Published) return release;
      if (release.status === ReleaseStatus.Staged && release.canaryPercentage > 0) {
        if (Math.random() * 100 < release.canaryPercentage) {
          return release;
        }
      }
    }

    return releases[0] || null;
  }

  getReleaseById(releaseId: string): Release | null {
    return this.releases.get(releaseId) || null;
  }

  getReleasesForApp(
    appName: string,
    channel?: UpdateChannel,
    status?: ReleaseStatus,
    limit: number = 10,
  ): Release[] {
    let releases = Array.from(this.releases.values())
      .filter((r) => r.appName === appName);

    if (channel) releases = releases.filter((r) => r.channel === channel);
    if (status) releases = releases.filter((r) => r.status === status);

    return releases
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      .slice(0, limit);
  }

  archiveRelease(releaseId: string): Release {
    const release = this.releases.get(releaseId);
    if (!release) {
      throw new Error(`Release not found: ${releaseId}`);
    }
    release.status = ReleaseStatus.Archived;
    this.releases.set(releaseId, release);
    return release;
  }

  getRollbackHistory(appName: string): Release[] {
    const history = this.rollbackHistory.get(appName) || [];
    return history
      .map((id) => this.releases.get(id))
      .filter((r): r is Release => r !== undefined)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }

  getCurrentDeploymentColor(): 'blue' | 'green' {
    return this.currentDeployment;
  }

  getAllReleases(): Release[] {
    return Array.from(this.releases.values());
  }

  clear(): void {
    this.releases.clear();
    this.stagedRollouts.clear();
    this.rollbackHistory.clear();
  }
}
