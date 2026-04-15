// NOTE: The production DB health check lives in backend/app/main.py
// (FastAPI /health/deep). This legacy Express shim no longer queries the
// database directly — the previous implementation pulled in `drizzle-orm`
// and a non-existent `../../drizzle/schema` module, which triggered a High
// Dependabot alert (SQL-injection via improperly escaped identifiers) and
// would also have failed at import time.

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: Date;
  checks: {
    database: HealthCheckResult;
    redis: HealthCheckResult;
    memory: HealthCheckResult;
    uptime: HealthCheckResult;
  };
  details?: string;
}

interface HealthCheckResult {
  status: 'ok' | 'warning' | 'error';
  responseTime: number;
  message?: string;
}

class HealthChecker {
  private lastCheckTime: Date = new Date();
  private consecutiveFailures: number = 0;
  private maxConsecutiveFailures: number = 3;

  async checkDatabase(): Promise<HealthCheckResult> {
    // The real DB health probe lives in the FastAPI backend
    // (backend/app/routes/health.py → /health/deep). This Express shim is
    // dev-only and no longer owns the database connection.
    return {
      status: 'ok',
      responseTime: 0,
      message: 'delegated to FastAPI /health/deep',
    };
  }

  async checkRedis(): Promise<HealthCheckResult> {
    const startTime = Date.now();
    try {
      // In production, connect to Redis and test PING
      // For now, return a placeholder
      const responseTime = Date.now() - startTime;

      return {
        status: 'ok',
        responseTime,
      };
    } catch (error) {
      return {
        status: 'error',
        responseTime: Date.now() - startTime,
        message: `Redis error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }

  checkMemory(): HealthCheckResult {
    const startTime = Date.now();
    try {
      const memUsage = process.memoryUsage();
      const heapUsedPercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;

      if (heapUsedPercent > 90) {
        return {
          status: 'error',
          responseTime: Date.now() - startTime,
          message: `Memory usage critical: ${heapUsedPercent.toFixed(2)}%`,
        };
      }

      if (heapUsedPercent > 75) {
        return {
          status: 'warning',
          responseTime: Date.now() - startTime,
          message: `Memory usage high: ${heapUsedPercent.toFixed(2)}%`,
        };
      }

      return {
        status: 'ok',
        responseTime: Date.now() - startTime,
      };
    } catch (error) {
      return {
        status: 'error',
        responseTime: Date.now() - startTime,
        message: `Memory check error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }

  checkUptime(): HealthCheckResult {
    const uptime = process.uptime();
    const responseTime = 0;

    if (uptime < 60) {
      return {
        status: 'warning',
        responseTime,
        message: 'Service recently started',
      };
    }

    return {
      status: 'ok',
      responseTime,
    };
  }

  async performHealthCheck(): Promise<HealthStatus> {
    const startTime = Date.now();

    const [database, redis, memory, uptime] = await Promise.all([
      this.checkDatabase(),
      this.checkRedis(),
      Promise.resolve(this.checkMemory()),
      Promise.resolve(this.checkUptime()),
    ]);

    const checks = { database, redis, memory, uptime };

    // Determine overall status
    const hasErrors = Object.values(checks).some(check => check.status === 'error');
    const hasWarnings = Object.values(checks).some(check => check.status === 'warning');

    let status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
    if (hasErrors) {
      status = 'unhealthy';
      this.consecutiveFailures++;
    } else if (hasWarnings) {
      status = 'degraded';
      this.consecutiveFailures = Math.max(0, this.consecutiveFailures - 1);
    } else {
      this.consecutiveFailures = 0;
    }

    this.lastCheckTime = new Date();

    const details = Object.entries(checks)
      .map(([key, check]) => `${key}: ${check.status}${check.message ? ` (${check.message})` : ''}`)
      .join('; ');

    return {
      status,
      timestamp: new Date(),
      checks,
      details,
    };
  }

  isHealthy(): boolean {
    return this.consecutiveFailures < this.maxConsecutiveFailures;
  }

  getLastCheckTime(): Date {
    return this.lastCheckTime;
  }

  getConsecutiveFailures(): number {
    return this.consecutiveFailures;
  }
}

export const healthChecker = new HealthChecker();
