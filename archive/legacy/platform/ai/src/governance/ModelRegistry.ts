import { v4 as uuidv4 } from 'uuid';

export enum ModelStatus {
  Development = 'development',
  Staging = 'staging',
  Production = 'production',
  Deprecated = 'deprecated',
  Retired = 'retired',
}

export enum ApprovalStatus {
  Pending = 'pending',
  Approved = 'approved',
  Rejected = 'rejected',
  ChangesRequested = 'changes_requested',
}

export interface ModelMetadata {
  name: string;
  version: string;
  description: string;
  author: string;
  date: Date;
  framework: string;
  taskType: string;
  inputSchema: Record<string, unknown>;
  outputSchema: Record<string, unknown>;
  performanceMetrics: Record<string, number>;
  license?: string;
  tags: string[];
}

export interface ModelVersion {
  id: string;
  version: string;
  metadata: ModelMetadata;
  status: ModelStatus;
  parentModelId: string | null;
  createdAt: Date;
  updatedAt: Date;
  checksum: string;
  artifactUri: string;
  deploymentHistory: DeploymentRecord[];
  approvalHistory: ApprovalRecord[];
}

export interface DeploymentRecord {
  id: string;
  environment: string;
  timestamp: Date;
  deployedBy: string;
  status: string;
  rollbackReason?: string;
}

export interface ApprovalRecord {
  id: string;
  reviewer: string;
  status: ApprovalStatus;
  comments: string;
  timestamp: Date;
  stage: string;
}

export interface LineageNode {
  modelId: string;
  version: string;
  name: string;
  parentId: string | null;
  children: LineageNode[];
}

export interface RegistryQuery {
  name?: string;
  version?: string;
  status?: ModelStatus;
  author?: string;
  tags?: string[];
  fromDate?: Date;
  toDate?: Date;
}

export class ModelRegistry {
  private models: Map<string, ModelVersion> = new Map();
  private lineageMap: Map<string, Set<string>> = new Map();

  register(
    metadata: ModelMetadata,
    artifactUri: string,
    checksum: string,
    parentModelId: string | null = null,
  ): ModelVersion {
    const id = uuidv4();
    const now = new Date();

    const model: ModelVersion = {
      id,
      version: metadata.version,
      metadata,
      status: ModelStatus.Development,
      parentModelId,
      createdAt: now,
      updatedAt: now,
      checksum,
      artifactUri,
      deploymentHistory: [],
      approvalHistory: [],
    };

    this.models.set(id, model);

    if (parentModelId) {
      const existing = this.lineageMap.get(parentModelId) || new Set();
      existing.add(id);
      this.lineageMap.set(parentModelId, existing);
    }

    return model;
  }

  getModel(id: string): ModelVersion | undefined {
    return this.models.get(id);
  }

  query(query: RegistryQuery): ModelVersion[] {
    const results: ModelVersion[] = [];
    for (const model of this.models.values()) {
      if (query.name && model.metadata.name !== query.name) continue;
      if (query.version && model.version !== query.version) continue;
      if (query.status && model.status !== query.status) continue;
      if (query.author && model.metadata.author !== query.author) continue;
      if (query.tags) {
        const hasAllTags = query.tags.every((t) => model.metadata.tags.includes(t));
        if (!hasAllTags) continue;
      }
      if (query.fromDate && model.createdAt < query.fromDate) continue;
      if (query.toDate && model.createdAt > query.toDate) continue;
      results.push(model);
    }
    return results;
  }

  updateStatus(id: string, status: ModelStatus): ModelVersion {
    const model = this.models.get(id);
    if (!model) throw new Error(`Model ${id} not found`);

    if (model.status === ModelStatus.Retired) {
      throw new Error(`Cannot update retired model ${id}`);
    }

    const validTransitions: Record<ModelStatus, ModelStatus[]> = {
      [ModelStatus.Development]: [ModelStatus.Staging],
      [ModelStatus.Staging]: [ModelStatus.Production, ModelStatus.Development],
      [ModelStatus.Production]: [ModelStatus.Deprecated],
      [ModelStatus.Deprecated]: [ModelStatus.Retired, ModelStatus.Production],
      [ModelStatus.Retired]: [],
    };

    const allowed = validTransitions[model.status];
    if (!allowed.includes(status)) {
      throw new Error(
        `Invalid transition from ${model.status} to ${status}. Allowed: ${allowed.join(', ')}`,
      );
    }

    model.status = status;
    model.updatedAt = new Date();
    return model;
  }

  addApprovalRecord(
    modelId: string,
    reviewer: string,
    status: ApprovalStatus,
    comments: string,
    stage: string,
  ): ApprovalRecord {
    const model = this.models.get(modelId);
    if (!model) throw new Error(`Model ${modelId} not found`);

    const record: ApprovalRecord = {
      id: uuidv4(),
      reviewer,
      status,
      comments,
      timestamp: new Date(),
      stage,
    };

    model.approvalHistory.push(record);
    model.updatedAt = new Date();
    return record;
  }

  recordDeployment(
    modelId: string,
    environment: string,
    deployedBy: string,
    status: string,
    rollbackReason?: string,
  ): DeploymentRecord {
    const model = this.models.get(modelId);
    if (!model) throw new Error(`Model ${modelId} not found`);

    const record: DeploymentRecord = {
      id: uuidv4(),
      environment,
      timestamp: new Date(),
      deployedBy,
      status,
      rollbackReason,
    };

    model.deploymentHistory.push(record);
    model.updatedAt = new Date();
    return record;
  }

  getLineage(modelId: string): LineageNode | null {
    const model = this.models.get(modelId);
    if (!model) return null;

    const childrenIds = this.lineageMap.get(modelId) || new Set();
    const children: LineageNode[] = [];

    for (const childId of childrenIds) {
      const childNode = this.getLineage(childId);
      if (childNode) children.push(childNode);
    }

    return {
      modelId: model.id,
      version: model.version,
      name: model.metadata.name,
      parentId: model.parentModelId,
      children,
    };
  }

  getAllVersions(modelName: string): ModelVersion[] {
    return this.query({ name: modelName }).sort(
      (a, b) => b.createdAt.getTime() - a.createdAt.getTime(),
    );
  }

  getLatestVersion(modelName: string, status?: ModelStatus): ModelVersion | undefined {
    const versions = this.getAllVersions(modelName);
    if (!versions.length) return undefined;
    if (!status) return versions[0];
    return versions.find((v) => v.status === status);
  }

  getProductionModels(): ModelVersion[] {
    return this.query({ status: ModelStatus.Production });
  }
}
