import { v4 as uuidv4 } from 'uuid';

type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  traceId: string;
  correlationId?: string;
  userId?: string;
  endpoint?: string;
  method?: string;
  statusCode?: number;
  responseTime?: number;
  message: string;
  data?: Record<string, any>;
  error?: {
    message: string;
    stack?: string;
    code?: string;
  };
  environment: string;
  version: string;
}

class StructuredLogger {
  private traceId: string = uuidv4();
  private correlationId?: string;
  private environment: string = process.env.NODE_ENV || 'development';
  private version: string = process.env.APP_VERSION || '1.0.0';
  private minLogLevel: LogLevel = (process.env.LOG_LEVEL as LogLevel) || 'info';

  private logLevels: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
    fatal: 4,
  };

  constructor() {
    this.traceId = uuidv4();
  }

  setTraceId(traceId: string): void {
    this.traceId = traceId;
  }

  setCorrelationId(correlationId: string): void {
    this.correlationId = correlationId;
  }

  getTraceId(): string {
    return this.traceId;
  }

  private shouldLog(level: LogLevel): boolean {
    return this.logLevels[level] >= this.logLevels[this.minLogLevel];
  }

  private formatLog(entry: LogEntry): string {
    return JSON.stringify(entry);
  }

  private log(
    level: LogLevel,
    message: string,
    data?: Record<string, any>,
    error?: Error
  ): void {
    if (!this.shouldLog(level)) return;

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      traceId: this.traceId,
      correlationId: this.correlationId,
      message,
      environment: this.environment,
      version: this.version,
      ...data,
    };

    if (error) {
      entry.error = {
        message: error.message,
        stack: error.stack,
        code: (error as any).code,
      };
    }

    const logOutput = this.formatLog(entry);

    if (level === 'error' || level === 'fatal') {
      console.error(logOutput);
    } else if (level === 'warn') {
      console.warn(logOutput);
    } else {
      console.log(logOutput);
    }
  }

  debug(message: string, data?: Record<string, any>): void {
    this.log('debug', message, data);
  }

  info(message: string, data?: Record<string, any>): void {
    this.log('info', message, data);
  }

  warn(message: string, data?: Record<string, any>): void {
    this.log('warn', message, data);
  }

  error(message: string, error?: Error, data?: Record<string, any>): void {
    this.log('error', message, data, error);
  }

  fatal(message: string, error?: Error, data?: Record<string, any>): void {
    this.log('fatal', message, data, error);
  }

  logRequest(
    method: string,
    endpoint: string,
    userId?: string,
    data?: Record<string, any>
  ): void {
    this.info('Request received', {
      method,
      endpoint,
      userId,
      ...data,
    });
  }

  logResponse(
    endpoint: string,
    statusCode: number,
    responseTime: number,
    data?: Record<string, any>
  ): void {
    const level = statusCode >= 400 ? 'warn' : 'info';
    this.log(level, 'Response sent', {
      endpoint,
      statusCode,
      responseTime,
      ...data,
    });
  }

  logDatabaseQuery(
    query: string,
    duration: number,
    rowsAffected?: number,
    error?: Error
  ): void {
    if (error) {
      this.error('Database query failed', error, {
        query: query.substring(0, 200), // Truncate long queries
        duration,
      });
    } else {
      const level = duration > 1000 ? 'warn' : 'debug';
      this.log(level, 'Database query executed', {
        query: query.substring(0, 200),
        duration,
        rowsAffected,
      });
    }
  }

  logCacheOperation(
    operation: 'get' | 'set' | 'delete',
    key: string,
    hit: boolean,
    duration: number
  ): void {
    this.debug('Cache operation', {
      operation,
      key,
      hit,
      duration,
    });
  }

  logSecurityEvent(
    event: string,
    severity: 'low' | 'medium' | 'high' | 'critical',
    userId?: string,
    data?: Record<string, any>
  ): void {
    const level = severity === 'critical' ? 'fatal' : severity === 'high' ? 'error' : 'warn';
    this.log(level, `Security event: ${event}`, {
      severity,
      userId,
      ...data,
    });
  }

  logAuditEvent(
    action: string,
    userId: string,
    resourceType: string,
    resourceId: string,
    changes?: Record<string, any>
  ): void {
    this.info('Audit event', {
      action,
      userId,
      resourceType,
      resourceId,
      changes,
    });
  }
}

export const structuredLogger = new StructuredLogger();
