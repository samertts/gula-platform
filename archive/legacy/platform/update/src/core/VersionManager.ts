import {
  AppVersion,
  UpdateChannel,
  VersionCompatibility,
  DependencyCompatibility,
  PlatformType,
} from '../types.js';

interface ParsedVersion {
  major: number;
  minor: number;
  patch: number;
  preRelease: string | null;
  buildMetadata: string | null;
}

export class VersionManager {
  private readonly appName: string;
  private readonly currentVersion: string;
  private readonly platform: PlatformType;
  private readonly channel: UpdateChannel;
  private versionCache: Map<string, ParsedVersion> = new Map();

  constructor(appName: string, currentVersion: string, platform: PlatformType, channel: UpdateChannel) {
    this.appName = appName;
    this.currentVersion = currentVersion;
    this.platform = platform;
    this.channel = channel;
  }

  parseVersion(version: string): ParsedVersion {
    const cached = this.versionCache.get(version);
    if (cached) return cached;

    const semverRegex = /^(\d+)\.(\d+)\.(\d+)(?:-([\w.-]+))?(?:\+([\w.-]+))?$/;
    const match = version.match(semverRegex);

    if (!match) {
      throw new Error(`Invalid semantic version string: "${version}"`);
    }

    const parsed: ParsedVersion = {
      major: parseInt(match[1], 10),
      minor: parseInt(match[2], 10),
      patch: parseInt(match[3], 10),
      preRelease: match[4] || null,
      buildMetadata: match[5] || null,
    };

    this.versionCache.set(version, parsed);
    return parsed;
  }

  compareVersions(a: string, b: string): number {
    const parsedA = this.parseVersion(a);
    const parsedB = this.parseVersion(b);

    if (parsedA.major !== parsedB.major) return parsedA.major - parsedB.major;
    if (parsedA.minor !== parsedB.minor) return parsedA.minor - parsedB.minor;
    if (parsedA.patch !== parsedB.patch) return parsedA.patch - parsedB.patch;

    const aPre = parsedA.preRelease;
    const bPre = parsedB.preRelease;

    if (aPre === null && bPre === null) return 0;
    if (aPre === null) return 1;
    if (bPre === null) return -1;

    const aParts = aPre.split('.');
    const bParts = bPre.split('.');

    for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {
      if (i >= aParts.length) return -1;
      if (i >= bParts.length) return 1;

      const aPart = aParts[i];
      const bPart = bParts[i];

      const aNum = parseInt(aPart, 10);
      const bNum = parseInt(bPart, 10);

      if (!isNaN(aNum) && !isNaN(bNum)) {
        if (aNum !== bNum) return aNum - bNum;
      } else {
        const cmp = aPart.localeCompare(bPart);
        if (cmp !== 0) return cmp;
      }
    }

    return 0;
  }

  isNewer(version: string, than: string): boolean {
    return this.compareVersions(version, than) > 0;
  }

  isOlder(version: string, than: string): boolean {
    return this.compareVersions(version, than) < 0;
  }

  isEqual(version: string, to: string): boolean {
    return this.compareVersions(version, to) === 0;
  }

  satisfies(version: string, range: string): boolean {
    const parsed = this.parseVersion(version);

    if (range.startsWith('^')) {
      const target = this.parseVersion(range.slice(1));
      return parsed.major === target.major && (
        parsed.minor > target.minor ||
        (parsed.minor === target.minor && parsed.patch >= target.patch)
      );
    }

    if (range.startsWith('~')) {
      const target = this.parseVersion(range.slice(1));
      return parsed.major === target.major && parsed.minor === target.minor && parsed.patch >= target.patch;
    }

    if (range.startsWith('>=')) {
      return this.compareVersions(version, range.slice(2)) >= 0;
    }

    if (range.startsWith('<=')) {
      return this.compareVersions(version, range.slice(2)) <= 0;
    }

    if (range.startsWith('>')) {
      return this.compareVersions(version, range.slice(1)) > 0;
    }

    if (range.startsWith('<')) {
      return this.compareVersions(version, range.slice(1)) < 0;
    }

    if (range.includes(' - ')) {
      const [low, high] = range.split(' - ');
      return this.compareVersions(version, low) >= 0 && this.compareVersions(version, high) <= 0;
    }

    if (range === '*') return true;

    if (range === 'x' || range === 'X') return true;

    const rangeParts = range.split('.');
    const verParts = version.split('.');

    for (let i = 0; i < Math.max(rangeParts.length, verParts.length); i++) {
      if (i >= rangeParts.length) break;
      if (rangeParts[i] === 'x' || rangeParts[i] === 'X' || rangeParts[i] === '*') break;
      if (i >= verParts.length) return false;
      if (parseInt(rangeParts[i], 10) !== parseInt(verParts[i], 10)) return false;
    }

    return true;
  }

  checkCompatibility(
    targetVersion: AppVersion,
    dependencyVersions: AppVersion[],
  ): VersionCompatibility {
    const currentParsed = this.parseVersion(this.currentVersion);
    const targetParsed = this.parseVersion(targetVersion.version);

    const minVersion = targetVersion.minAppVersion || targetVersion.version;
    const compatible = this.compareVersions(this.currentVersion, minVersion) >= 0;

    const deps: DependencyCompatibility[] = dependencyVersions.map((dep) => {
      const depCompatible = dep.minAppVersion
        ? this.compareVersions(dep.version, dep.minAppVersion) >= 0
        : true;
      return {
        name: dep.appName,
        currentVersion: dep.version,
        requiredVersion: dep.minAppVersion || dep.version,
        compatible: depCompatible,
      };
    });

    let reason: string | null = null;
    if (!compatible) {
      reason = `Current version ${this.currentVersion} does not satisfy minimum required version ${minVersion}`;
    }

    const failedDep = deps.find((d) => !d.compatible);
    if (!reason && failedDep) {
      reason = `Dependency ${failedDep.name} version ${failedDep.currentVersion} does not satisfy requirement ${failedDep.requiredVersion}`;
    }

    const channelCompatible = this.isChannelAllowed(targetVersion.channel);
    if (!reason && !channelCompatible) {
      reason = `Channel ${targetVersion.channel} is not accessible from current channel ${this.channel}`;
    }

    return {
      compatible: compatible && !failedDep && channelCompatible,
      currentVersion: this.currentVersion,
      requiredVersion: targetVersion.version,
      reason,
      dependencies: deps,
    };
  }

  private isChannelAllowed(channel: UpdateChannel): boolean {
    const hierarchy: Record<UpdateChannel, number> = {
      [UpdateChannel.Stable]: 0,
      [UpdateChannel.Beta]: 1,
      [UpdateChannel.Canary]: 2,
      [UpdateChannel.Alpha]: 3,
    };

    return hierarchy[channel] <= hierarchy[this.channel];
  }

  async getVersionMatrix(availableVersions: AppVersion[]): Promise<AppVersion[]> {
    const channelFiltered = availableVersions.filter((v) => this.isChannelAllowed(v.channel));
    const compatible = channelFiltered.filter((v) => {
      if (!v.minAppVersion) return true;
      try {
        return this.compareVersions(this.currentVersion, v.minAppVersion) >= 0;
      } catch {
        return false;
      }
    });

    compatible.sort((a, b) => this.compareVersions(b.version, a.version));
    return compatible;
  }

  getNextVersion(availableVersions: AppVersion[]): AppVersion | null {
    const validChannels = availableVersions.filter((v) => {
      if (!this.isNewer(v.version, this.currentVersion)) return false;
      if (v.minAppVersion && this.isOlder(this.currentVersion, v.minAppVersion)) return false;
      return this.isChannelAllowed(v.channel);
    });

    if (validChannels.length === 0) return null;

    validChannels.sort((a, b) => this.compareVersions(b.version, a.version));
    return validChannels[0];
  }

  clearCache(): void {
    this.versionCache.clear();
  }
}
