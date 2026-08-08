import {
  UpdatePackage,
  UpdateError,
  UpdateErrorCode,
  VersionCompatibility,
} from '../types.js';
import { VersionManager } from './VersionManager.js';
import { PackageSigner } from '../platform/PackageSigner.js';

export interface ValidationResult {
  valid: boolean;
  errors: UpdateError[];
  warnings: string[];
  checks: {
    integrity: boolean;
    signature: boolean;
    compatibility: boolean;
    storage: boolean;
    dependencies: boolean;
  };
}

export interface PreUpdateCheck {
  name: string;
  check: () => Promise<{ passed: boolean; message?: string }>;
}

export interface PostUpdateCheck {
  name: string;
  check: () => Promise<{ passed: boolean; message?: string }>;
}

export class UpdateValidator {
  private readonly versionManager: VersionManager;
  private readonly packageSigner: PackageSigner;
  private preUpdateChecks: PreUpdateCheck[] = [];
  private postUpdateChecks: PostUpdateCheck[] = [];

  constructor(versionManager: VersionManager, packageSigner: PackageSigner) {
    this.versionManager = versionManager;
    this.packageSigner = packageSigner;
  }

  registerPreUpdateCheck(check: PreUpdateCheck): void {
    this.preUpdateChecks.push(check);
  }

  registerPostUpdateCheck(check: PostUpdateCheck): void {
    this.postUpdateChecks.push(check);
  }

  async validate(updatePackage: UpdatePackage): Promise<ValidationResult> {
    const errors: UpdateError[] = [];
    const warnings: string[] = [];

    const integrityResult = await this.verifyIntegrity(updatePackage);
    if (!integrityResult.passed) {
      errors.push({
        code: UpdateErrorCode.ChecksumMismatch,
        message: integrityResult.message || 'Package integrity check failed',
        details: `Expected checksum: ${updatePackage.checksum}`,
        recoverable: true,
      });
    }

    const signatureResult = await this.verifySignature(updatePackage);
    if (!signatureResult.passed) {
      errors.push({
        code: UpdateErrorCode.SignatureInvalid,
        message: signatureResult.message || 'Package signature verification failed',
        details: `Signature: ${updatePackage.signature.slice(0, 32)}...`,
        recoverable: false,
      });
    }

    const compatResult = await this.verifyCompatibility(updatePackage);
    if (!compatResult.passed) {
      errors.push({
        code: UpdateErrorCode.IncompatibleVersion,
        message: compatResult.message || 'Version compatibility check failed',
        details: null,
        recoverable: false,
      });
    }

    const storageResult = await this.checkStorage(updatePackage);
    if (!storageResult.passed) {
      errors.push({
        code: UpdateErrorCode.InsufficientStorage,
        message: storageResult.message || 'Insufficient storage for update',
        details: `Required: ${updatePackage.size} bytes`,
        recoverable: true,
      });
    }

    const depResult = await this.checkDependencies(updatePackage);
    if (!depResult.passed) {
      warnings.push(depResult.message || 'Dependency check produced warnings');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      checks: {
        integrity: integrityResult.passed,
        signature: signatureResult.passed,
        compatibility: compatResult.passed,
        storage: storageResult.passed,
        dependencies: depResult.passed,
      },
    };
  }

  private async verifyIntegrity(pkg: UpdatePackage): Promise<{ passed: boolean; message?: string }> {
    try {
      const algorithm = pkg.checksumAlgorithm === 'sha512' ? 'SHA-512' : 'SHA-256';
      const response = await fetch(pkg.downloadUrl, { method: 'HEAD' });
      if (!response.ok) {
        return { passed: false, message: `Cannot access package at ${pkg.downloadUrl}` };
      }

      const contentLength = response.headers.get('content-length');
      if (contentLength && parseInt(contentLength, 10) !== pkg.size) {
        return { passed: false, message: `Size mismatch: expected ${pkg.size}, got ${contentLength}` };
      }

      return { passed: true };
    } catch (error) {
      return { passed: false, message: `Integrity check error: ${(error as Error).message}` };
    }
  }

  private async verifySignature(pkg: UpdatePackage): Promise<{ passed: boolean; message?: string }> {
    try {
      const valid = await this.packageSigner.verifySignature(
        pkg.downloadUrl,
        pkg.signature,
        pkg.signerCertificate,
      );
      if (!valid) {
        return { passed: false, message: 'Cryptographic signature verification failed' };
      }
      return { passed: true };
    } catch (error) {
      return { passed: false, message: `Signature verification error: ${(error as Error).message}` };
    }
  }

  private async verifyCompatibility(pkg: UpdatePackage): Promise<{ passed: boolean; message?: string }> {
    try {
      const compatCheck: VersionCompatibility = this.versionManager.checkCompatibility(
        {
          appName: pkg.appName,
          version: pkg.version,
          buildNumber: pkg.buildNumber,
          platform: pkg.platform,
          releaseDate: pkg.releaseDate,
          minAppVersion: pkg.minAppVersion,
          channel: pkg.channel,
        },
        [],
      );

      if (!compatCheck.compatible) {
        return { passed: false, message: compatCheck.reason || 'Incompatible version' };
      }

      return { passed: true };
    } catch (error) {
      return { passed: false, message: `Compatibility check error: ${(error as Error).message}` };
    }
  }

  private async checkStorage(pkg: UpdatePackage): Promise<{ passed: boolean; message?: string }> {
    const requiredSpace = pkg.size * 2.5;
    let availableSpace = 0;

    if (typeof navigator !== 'undefined' && 'storage' in navigator) {
      try {
        const estimate = await navigator.storage.estimate();
        availableSpace = (estimate.quota || 0) - (estimate.usage || 0);
      } catch {
        availableSpace = Infinity;
      }
    } else {
      availableSpace = pkg.size * 10;
    }

    if (availableSpace < requiredSpace) {
      return {
        passed: false,
        message: `Need ${this.formatBytes(requiredSpace)} but only ${this.formatBytes(availableSpace)} available`,
      };
    }

    return { passed: true };
  }

  private async checkDependencies(pkg: UpdatePackage): Promise<{ passed: boolean; message?: string }> {
    if (!pkg.requires || pkg.requires.length === 0) {
      return { passed: true };
    }

    const unsatisfied: string[] = [];
    for (const requirement of pkg.requires) {
      if (!this.versionManager.satisfies(this.versionManager['currentVersion'], requirement)) {
        unsatisfied.push(requirement);
      }
    }

    if (unsatisfied.length > 0) {
      return {
        passed: false,
        message: `Unsatisfied dependencies: ${unsatisfied.join(', ')}`,
      };
    }

    return { passed: true };
  }

  async runPreUpdateChecks(): Promise<{ passed: boolean; errors: string[] }> {
    const errors: string[] = [];
    for (const check of this.preUpdateChecks) {
      try {
        const result = await check.check();
        if (!result.passed) {
          errors.push(`${check.name}: ${result.message || 'failed'}`);
        }
      } catch (error) {
        errors.push(`${check.name}: ${(error as Error).message}`);
      }
    }
    return { passed: errors.length === 0, errors };
  }

  async runPostUpdateChecks(): Promise<{ passed: boolean; errors: string[] }> {
    const errors: string[] = [];
    for (const check of this.postUpdateChecks) {
      try {
        const result = await check.check();
        if (!result.passed) {
          errors.push(`${check.name}: ${result.message || 'failed'}`);
        }
      } catch (error) {
        errors.push(`${check.name}: ${(error as Error).message}`);
      }
    }
    return { passed: errors.length === 0, errors };
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
  }
}
