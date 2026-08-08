import { v4 as uuidv4 } from 'uuid';

export enum PromptStatus {
  Draft = 'draft',
  Testing = 'testing',
  Approved = 'approved',
  Deprecated = 'deprecated',
  Retired = 'retired',
}

export enum TestResult {
  Pass = 'pass',
  Fail = 'fail',
  Warning = 'warning',
}

export interface PromptVariable {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  defaultValue?: unknown;
  validation?: string;
}

export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  systemPrompt: string;
  userPromptTemplate: string;
  variables: PromptVariable[];
  model: string;
  temperature: number;
  maxTokens: number;
  stopSequences: string[];
  locale: 'ar' | 'en' | 'both';
}

export interface PromptVersion {
  id: string;
  version: string;
  templateId: string;
  template: PromptTemplate;
  status: PromptStatus;
  changeNotes: string;
  author: string;
  createdAt: Date;
  updatedAt: Date;
  testResults: PromptTestResult[];
  approvals: PromptApproval[];
  optimizationHistory: OptimizationRecord[];
}

export interface PromptTestResult {
  id: string;
  testCase: string;
  input: Record<string, unknown>;
  expectedOutput: string;
  actualOutput: string;
  result: TestResult;
  latency: number;
  timestamp: Date;
  notes?: string;
}

export interface PromptApproval {
  id: string;
  reviewer: string;
  status: 'approved' | 'rejected' | 'changes_requested';
  comments: string;
  timestamp: Date;
}

export interface OptimizationRecord {
  id: string;
  type: string;
  beforeScore: number;
  afterScore: number;
  changes: string;
  performedBy: string;
  timestamp: Date;
}

export interface PromptRegistryConfig {
  requireApproval: boolean;
  requireTesting: boolean;
  maxVersionsPerTemplate: number;
  auditEnabled: boolean;
}

const DEFAULT_CONFIG: PromptRegistryConfig = {
  requireApproval: true,
  requireTesting: true,
  maxVersionsPerTemplate: 20,
  auditEnabled: true,
};

export class PromptRegistry {
  private templates: Map<string, PromptTemplate> = new Map();
  private versions: Map<string, PromptVersion[]> = new Map();
  private config: PromptRegistryConfig;
  private auditLog: AuditEntry[] = [];

  constructor(config: Partial<PromptRegistryConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  registerTemplate(
    template: Omit<PromptTemplate, 'id'>,
    author: string,
    changeNotes: string = 'Initial version',
  ): PromptVersion {
    const templateId = uuidv4();
    const fullTemplate: PromptTemplate = { id: templateId, ...template };
    this.templates.set(templateId, fullTemplate);

    return this.createVersion(templateId, author, changeNotes);
  }

  createVersion(
    templateId: string,
    author: string,
    changeNotes: string,
  ): PromptVersion {
    const template = this.templates.get(templateId);
    if (!template) throw new Error(`Template ${templateId} not found`);

    const existingVersions = this.versions.get(templateId) || [];

    if (existingVersions.length >= this.config.maxVersionsPerTemplate) {
      throw new Error(
        `Version limit (${this.config.maxVersionsPerTemplate}) reached for template ${templateId}`,
      );
    }

    const versionNumber = existingVersions.length + 1;
    const version: PromptVersion = {
      id: uuidv4(),
      version: `v${versionNumber}`,
      templateId,
      template: { ...template },
      status: PromptStatus.Draft,
      changeNotes,
      author,
      createdAt: new Date(),
      updatedAt: new Date(),
      testResults: [],
      approvals: [],
      optimizationHistory: [],
    };

    existingVersions.push(version);
    this.versions.set(templateId, existingVersions);

    if (this.config.auditEnabled) {
      this.auditLog.push({
        id: uuidv4(),
        action: 'version_created',
        entityId: version.id,
        entityType: 'prompt_version',
        actor: author,
        details: { templateId, version: version.version, changeNotes },
        timestamp: version.createdAt,
      });
    }

    return version;
  }

  updateTemplate(id: string, updates: Partial<PromptTemplate>): PromptTemplate {
    const template = this.templates.get(id);
    if (!template) throw new Error(`Template ${id} not found`);

    Object.assign(template, updates);
    return template;
  }

  getTemplate(id: string): PromptTemplate | undefined {
    return this.templates.get(id);
  }

  getVersion(id: string): PromptVersion | undefined {
    for (const versions of this.versions.values()) {
      const found = versions.find((v) => v.id === id);
      if (found) return found;
    }
    return undefined;
  }

  getVersions(templateId: string): PromptVersion[] {
    return this.versions.get(templateId) || [];
  }

  getLatestVersion(templateId: string, approvedOnly: boolean = true): PromptVersion | undefined {
    const versions = this.versions.get(templateId) || [];
    if (approvedOnly) {
      return versions
        .filter((v) => v.status === PromptStatus.Approved)
        .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())[0];
    }
    return versions.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime())[0];
  }

  async testPrompt(
    versionId: string,
    testCase: string,
    input: Record<string, unknown>,
    expectedOutput: string,
    executor: (prompt: string, variables: Record<string, unknown>) => Promise<string>,
  ): Promise<PromptTestResult> {
    const version = this.getVersion(versionId);
    if (!version) throw new Error(`Version ${versionId} not found`);

    const startTime = Date.now();
    let actualOutput: string;
    try {
      actualOutput = await executor(
        version.template.userPromptTemplate,
        input,
      );
    } catch (error) {
      actualOutput = `ERROR: ${error instanceof Error ? error.message : String(error)}`;
    }
    const latency = Date.now() - startTime;

    const result: TestResult =
      actualOutput === expectedOutput
        ? TestResult.Pass
        : actualOutput.startsWith('ERROR')
          ? TestResult.Fail
          : TestResult.Warning;

    const testResult: PromptTestResult = {
      id: uuidv4(),
      testCase,
      input,
      expectedOutput,
      actualOutput,
      result,
      latency,
      timestamp: new Date(),
    };

    version.testResults.push(testResult);

    if (this.config.auditEnabled) {
      this.auditLog.push({
        id: uuidv4(),
        action: 'prompt_tested',
        entityId: versionId,
        entityType: 'prompt_test',
        actor: 'system',
        details: { testCase, result: result.toString() },
        timestamp: testResult.timestamp,
      });
    }

    return testResult;
  }

  approve(
    versionId: string,
    reviewer: string,
    status: 'approved' | 'rejected' | 'changes_requested',
    comments: string,
  ): PromptApproval {
    const version = this.getVersion(versionId);
    if (!version) throw new Error(`Version ${versionId} not found`);

    const approval: PromptApproval = {
      id: uuidv4(),
      reviewer,
      status,
      comments,
      timestamp: new Date(),
    };

    version.approvals.push(approval);

    if (status === 'approved') {
      version.status = PromptStatus.Approved;
    } else if (status === 'rejected') {
      version.status = PromptStatus.Draft;
    }

    version.updatedAt = new Date();

    if (this.config.auditEnabled) {
      this.auditLog.push({
        id: uuidv4(),
        action: `prompt_${status}`,
        entityId: versionId,
        entityType: 'prompt_approval',
        actor: reviewer,
        details: { status, comments },
        timestamp: approval.timestamp,
      });
    }

    return approval;
  }

  recordOptimization(
    versionId: string,
    type: string,
    beforeScore: number,
    afterScore: number,
    changes: string,
    performedBy: string,
  ): OptimizationRecord {
    const version = this.getVersion(versionId);
    if (!version) throw new Error(`Version ${versionId} not found`);

    const record: OptimizationRecord = {
      id: uuidv4(),
      type,
      beforeScore,
      afterScore,
      changes,
      performedBy,
      timestamp: new Date(),
    };

    version.optimizationHistory.push(record);
    return record;
  }

  deprecate(versionId: string): PromptVersion {
    const version = this.getVersion(versionId);
    if (!version) throw new Error(`Version ${versionId} not found`);
    version.status = PromptStatus.Deprecated;
    version.updatedAt = new Date();
    return version;
  }

  getAuditLog(
    options: { entityId?: string; action?: string; fromDate?: Date; toDate?: Date } = {},
  ): AuditEntry[] {
    let entries = this.auditLog;
    if (options.entityId) {
      entries = entries.filter((e) => e.entityId === options.entityId);
    }
    if (options.action) {
      entries = entries.filter((e) => e.action === options.action);
    }
    if (options.fromDate) {
      entries = entries.filter((e) => e.timestamp >= options.fromDate!);
    }
    if (options.toDate) {
      entries = entries.filter((e) => e.timestamp <= options.toDate!);
    }
    return entries.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }
}

interface AuditEntry {
  id: string;
  action: string;
  entityId: string;
  entityType: string;
  actor: string;
  details: Record<string, unknown>;
  timestamp: Date;
}
