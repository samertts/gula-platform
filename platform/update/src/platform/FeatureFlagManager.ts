import { FeatureFlag, FlagCondition } from '../types.js';

export interface FeatureFlagContext {
  userId?: string;
  groupId?: string;
  labId?: string;
  region?: string;
  version?: string;
  platform?: string;
  randomSeed?: number;
  custom?: Record<string, string>;
}

type FlagChangeListener = (flag: FeatureFlag, previous: FeatureFlag) => void;

export class FeatureFlagManager {
  private flags: Map<string, FeatureFlag> = new Map();
  private remoteEndpoint: string | null = null;
  private refreshInterval: ReturnType<typeof setInterval> | null = null;
  private listeners: Map<string, Set<FlagChangeListener>> = new Map();
  private evaluationCache: Map<string, boolean> = new Map();

  constructor(remoteEndpoint?: string) {
    if (remoteEndpoint) {
      this.remoteEndpoint = remoteEndpoint;
    }
  }

  registerFlag(flag: FeatureFlag): void {
    this.flags.set(flag.key, flag);
    this.evaluationCache.delete(flag.key);
  }

  registerFlags(flags: FeatureFlag[]): void {
    for (const flag of flags) {
      this.registerFlag(flag);
    }
  }

  removeFlag(key: string): boolean {
    const removed = this.flags.delete(key);
    this.evaluationCache.delete(key);
    return removed;
  }

  getFlag(key: string): FeatureFlag | undefined {
    return this.flags.get(key);
  }

  getAllFlags(): FeatureFlag[] {
    return Array.from(this.flags.values());
  }

  isEnabled(key: string, context?: FeatureFlagContext): boolean {
    const cacheKey = this.getCacheKey(key, context);
    const cached = this.evaluationCache.get(cacheKey);
    if (cached !== undefined) return cached;

    const flag = this.flags.get(key);
    if (!flag) return false;
    if (!flag.enabled) return false;

    if (flag.rolloutPercentage < 100) {
      const seed = context?.randomSeed ?? this.hashKey(context?.userId || key);
      const percentage = seed % 100;
      if (percentage >= flag.rolloutPercentage) {
        this.evaluationCache.set(cacheKey, false);
        return false;
      }
    }

    if (flag.conditions.length > 0) {
      const conditionsMet = this.evaluateConditions(flag.conditions, context);
      if (!conditionsMet) {
        this.evaluationCache.set(cacheKey, false);
        return false;
      }
    }

    this.evaluationCache.set(cacheKey, true);
    return true;
  }

  setEnabled(key: string, enabled: boolean): void {
    const flag = this.flags.get(key);
    if (!flag) {
      throw new Error(`Flag not found: ${key}`);
    }
    const previous = { ...flag };
    flag.enabled = enabled;
    this.flags.set(key, flag);
    this.evaluationCache.delete(key);
    this.notifyListeners(key, flag, previous);
  }

  setRolloutPercentage(key: string, percentage: number): void {
    if (percentage < 0 || percentage > 100) {
      throw new Error('Rollout percentage must be between 0 and 100');
    }
    const flag = this.flags.get(key);
    if (!flag) {
      throw new Error(`Flag not found: ${key}`);
    }
    const previous = { ...flag };
    flag.rolloutPercentage = percentage;
    this.flags.set(key, flag);
    this.evaluationCache.delete(key);
    this.notifyListeners(key, flag, previous);
  }

  addCondition(key: string, condition: FlagCondition): void {
    const flag = this.flags.get(key);
    if (!flag) {
      throw new Error(`Flag not found: ${key}`);
    }
    const previous = { ...flag };
    flag.conditions.push(condition);
    this.flags.set(key, flag);
    this.evaluationCache.delete(key);
    this.notifyListeners(key, flag, previous);
  }

  removeCondition(key: string, conditionIndex: number): void {
    const flag = this.flags.get(key);
    if (!flag) {
      throw new Error(`Flag not found: ${key}`);
    }
    const previous = { ...flag };
    flag.conditions.splice(conditionIndex, 1);
    this.flags.set(key, flag);
    this.evaluationCache.delete(key);
    this.notifyListeners(key, flag, previous);
  }

  async refreshFromRemote(): Promise<void> {
    if (!this.remoteEndpoint) return;

    try {
      const response = await fetch(this.remoteEndpoint, {
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch flags: ${response.status}`);
      }

      const remoteFlags: FeatureFlag[] = await response.json();
      for (const flag of remoteFlags) {
        const existing = this.flags.get(flag.key);
        if (existing) {
          const previous = { ...existing };
          const updated = { ...existing, ...flag };
          this.flags.set(flag.key, updated);
          this.evaluationCache.delete(flag.key);
          this.notifyListeners(flag.key, updated, previous);
        } else {
          this.flags.set(flag.key, flag);
        }
      }
    } catch (error) {
      console.warn('Failed to refresh feature flags from remote:', error);
    }
  }

  startAutoRefresh(intervalMs: number = 300000): void {
    this.stopAutoRefresh();
    this.refreshFromRemote();
    this.refreshInterval = setInterval(() => {
      this.refreshFromRemote();
    }, intervalMs);
  }

  stopAutoRefresh(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  onChange(key: string, listener: FlagChangeListener): () => void {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }
    this.listeners.get(key)!.add(listener);
    return () => {
      this.listeners.get(key)?.delete(listener);
    };
  }

  clearEvaluationCache(): void {
    this.evaluationCache.clear();
  }

  private evaluateConditions(
    conditions: FlagCondition[],
    context?: FeatureFlagContext,
  ): boolean {
    if (!context) return conditions.length === 0;

    return conditions.every((condition) => {
      const contextValue = this.getContextValue(condition.type, context);
      if (contextValue === undefined) return false;

      return this.evaluateCondition(contextValue, condition.operator, condition.value);
    });
  }

  private getContextValue(type: FlagCondition['type'], context: FeatureFlagContext): string | undefined {
    switch (type) {
      case 'user': return context.userId;
      case 'group': return context.groupId;
      case 'lab': return context.labId;
      case 'region': return context.region;
      case 'version': return context.version;
      case 'platform': return context.platform;
      case 'random':
        const seed = context.randomSeed ?? this.hashKey(context.userId || 'default');
        return String(seed % 100);
      default: return undefined;
    }
  }

  private evaluateCondition(
    contextValue: string,
    operator: FlagCondition['operator'],
    targetValue: string | string[] | number,
  ): boolean {
    const target = typeof targetValue === 'string' ? targetValue : String(targetValue);
    const targetArray = Array.isArray(targetValue)
      ? targetValue.map(String)
      : [targetValue].map(String);

    switch (operator) {
      case 'eq': return contextValue === target;
      case 'neq': return contextValue !== target;
      case 'in': return targetArray.includes(contextValue);
      case 'nin': return !targetArray.includes(contextValue);
      case 'gte': return parseFloat(contextValue) >= parseFloat(target);
      case 'lte': return parseFloat(contextValue) <= parseFloat(target);
      case 'contains': return contextValue.includes(target);
      default: return false;
    }
  }

  private hashKey(key: string): number {
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      const char = key.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash);
  }

  private getCacheKey(key: string, context?: FeatureFlagContext): string {
    if (!context) return key;
    const contextStr = [
      context.userId,
      context.groupId,
      context.labId,
      context.region,
      context.version,
      context.platform,
    ].filter(Boolean).join(':');
    return `${key}:${contextStr}`;
  }

  private notifyListeners(key: string, flag: FeatureFlag, previous: FeatureFlag): void {
    const handlers = this.listeners.get(key);
    if (handlers) {
      handlers.forEach((handler) => handler(flag, previous));
    }
  }

  destroy(): void {
    this.stopAutoRefresh();
    this.flags.clear();
    this.listeners.clear();
    this.evaluationCache.clear();
  }
}
