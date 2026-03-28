import { Request } from 'express';

interface RateLimitConfig {
  perIP: number;
  perUser: number;
  perEndpoint: number;
  loginAttempts: number;
  windowMs: number;
}

interface RateLimitStore {
  [key: string]: {
    count: number;
    resetTime: number;
  };
}

class AdvancedRateLimiter {
  private ipStore: RateLimitStore = {};
  private userStore: RateLimitStore = {};
  private endpointStore: RateLimitStore = {};
  private loginStore: RateLimitStore = {};

  private config: RateLimitConfig = {
    perIP: 50,
    perUser: 100,
    perEndpoint: 1000,
    loginAttempts: 5,
    windowMs: 60000, // 1 minute
  };

  constructor(config?: Partial<RateLimitConfig>) {
    if (config) {
      this.config = { ...this.config, ...config };
    }

    // Cleanup old entries every 5 minutes
    setInterval(() => this.cleanup(), 5 * 60 * 1000);
  }

  private getKey(prefix: string, value: string): string {
    return `${prefix}:${value}`;
  }

  private isRateLimited(store: RateLimitStore, key: string, limit: number): boolean {
    const now = Date.now();
    const entry = store[key];

    if (!entry || now > entry.resetTime) {
      store[key] = {
        count: 1,
        resetTime: now + this.config.windowMs,
      };
      return false;
    }

    entry.count++;
    return entry.count > limit;
  }

  private cleanup(): void {
    const now = Date.now();

    const cleanStore = (store: RateLimitStore) => {
      Object.keys(store).forEach(key => {
        if (store[key].resetTime < now) {
          delete store[key];
        }
      });
    };

    cleanStore(this.ipStore);
    cleanStore(this.userStore);
    cleanStore(this.endpointStore);
    cleanStore(this.loginStore);
  }

  checkIPLimit(ip: string): { limited: boolean; remaining: number } {
    const key = this.getKey('ip', ip);
    const limited = this.isRateLimited(this.ipStore, key, this.config.perIP);
    const remaining = Math.max(0, this.config.perIP - (this.ipStore[key]?.count || 0));

    return { limited, remaining };
  }

  checkUserLimit(userId: string): { limited: boolean; remaining: number } {
    const key = this.getKey('user', userId);
    const limited = this.isRateLimited(this.userStore, key, this.config.perUser);
    const remaining = Math.max(0, this.config.perUser - (this.userStore[key]?.count || 0));

    return { limited, remaining };
  }

  checkEndpointLimit(endpoint: string): { limited: boolean; remaining: number } {
    const key = this.getKey('endpoint', endpoint);
    const limited = this.isRateLimited(this.endpointStore, key, this.config.perEndpoint);
    const remaining = Math.max(0, this.config.perEndpoint - (this.endpointStore[key]?.count || 0));

    return { limited, remaining };
  }

  checkLoginLimit(identifier: string): { limited: boolean; remaining: number } {
    const key = this.getKey('login', identifier);
    const limited = this.isRateLimited(this.loginStore, key, this.config.loginAttempts);
    const remaining = Math.max(0, this.config.loginAttempts - (this.loginStore[key]?.count || 0));

    return { limited, remaining };
  }

  checkAllLimits(
    req: Request,
    userId?: string,
    endpoint?: string
  ): {
    limited: boolean;
    reason?: string;
    remaining: Record<string, number>;
  } {
    const ip = req.ip || req.socket.remoteAddress || 'unknown';

    const ipCheck = this.checkIPLimit(ip);
    const endpointCheck = endpoint ? this.checkEndpointLimit(endpoint) : { limited: false, remaining: Infinity };
    const userCheck = userId ? this.checkUserLimit(userId) : { limited: false, remaining: Infinity };

    const remaining = {
      ip: ipCheck.remaining,
      endpoint: endpointCheck.remaining,
      user: userCheck.remaining,
    };

    if (ipCheck.limited) {
      return {
        limited: true,
        reason: 'IP rate limit exceeded',
        remaining,
      };
    }

    if (endpointCheck.limited) {
      return {
        limited: true,
        reason: 'Endpoint rate limit exceeded',
        remaining,
      };
    }

    if (userCheck.limited) {
      return {
        limited: true,
        reason: 'User rate limit exceeded',
        remaining,
      };
    }

    return {
      limited: false,
      remaining,
    };
  }

  getStats(): {
    totalIPKeys: number;
    totalUserKeys: number;
    totalEndpointKeys: number;
    totalLoginAttempts: number;
  } {
    return {
      totalIPKeys: Object.keys(this.ipStore).length,
      totalUserKeys: Object.keys(this.userStore).length,
      totalEndpointKeys: Object.keys(this.endpointStore).length,
      totalLoginAttempts: Object.keys(this.loginStore).length,
    };
  }

  reset(): void {
    this.ipStore = {};
    this.userStore = {};
    this.endpointStore = {};
    this.loginStore = {};
  }
}

export const advancedRateLimiter = new AdvancedRateLimiter({
  perIP: 50,
  perUser: 100,
  perEndpoint: 1000,
  loginAttempts: 5,
  windowMs: 60000,
});
