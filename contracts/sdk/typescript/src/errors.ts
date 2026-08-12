export class GulaError extends Error {
  public readonly statusCode: number;
  public readonly code: string;
  public readonly details?: unknown;

  constructor(message: string, statusCode: number, code: string, details?: unknown) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class AuthenticationError extends GulaError {
  constructor(message = 'Authentication required', details?: unknown) {
    super(message, 401, 'UNAUTHORIZED', details);
  }
}

export class PermissionError extends GulaError {
  constructor(message = 'Insufficient permissions', details?: unknown) {
    super(message, 403, 'FORBIDDEN', details);
  }
}

export class NotFoundError extends GulaError {
  constructor(message = 'Resource not found', details?: unknown) {
    super(message, 404, 'NOT_FOUND', details);
  }
}

export class ConflictError extends GulaError {
  constructor(message = 'Resource conflict', details?: unknown) {
    super(message, 409, 'CONFLICT', details);
  }
}

export class RateLimitError extends GulaError {
  public readonly retryAfter: number;

  constructor(message = 'Rate limit exceeded', retryAfter = 60, details?: unknown) {
    super(message, 429, 'RATE_LIMITED', details);
    this.retryAfter = retryAfter;
  }
}

export class ValidationError extends GulaError {
  public readonly errors: Record<string, string[]>;

  constructor(message = 'Validation failed', errors: Record<string, string[]> = {}, details?: unknown) {
    super(message, 422, 'VALIDATION_ERROR', details);
    this.errors = errors;
  }
}

export class ServerError extends GulaError {
  constructor(message = 'Internal server error', details?: unknown) {
    super(message, 500, 'SERVER_ERROR', details);
  }
}

export const errorFromStatus = (status: number, body: any): GulaError => {
  const detail = body?.detail ?? body?.message ?? body;
  switch (status) {
    case 401: return new AuthenticationError(typeof detail === 'string' ? detail : undefined, body);
    case 403: return new PermissionError(typeof detail === 'string' ? detail : undefined, body);
    case 404: return new NotFoundError(typeof detail === 'string' ? detail : undefined, body);
    case 409: return new ConflictError(typeof detail === 'string' ? detail : undefined, body);
    case 422: return new ValidationError(typeof detail === 'string' ? detail : undefined, body?.errors ?? {}, body);
    case 429: return new RateLimitError(undefined, body?.retry_after ?? 60, body);
    default: return new GulaError(
      typeof detail === 'string' ? detail : `HTTP ${status}`,
      status,
      `HTTP_${status}`,
      body
    );
  }
};
