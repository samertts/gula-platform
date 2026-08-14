import axios from "axios";
import { api } from "./client";

export const SCOPED_READ_CONTRACTS = {
  patients: {
    id: "patients.read",
    path: "/api/v1/clinical/patients",
    permission: "patients.read",
  },
  orders: {
    id: "orders.read",
    path: "/api/v1/clinical/orders",
    permission: "orders.read",
  },
} as const;

/** Legacy `/patients` and `/lims/orders` REST surfaces remain blocked forever
 * for frontend-v3. Reads can use only the versioned canonical gateway below. */
export const DIRECT_REST_SCOPED_READS_BLOCKED = true;

type JsonRecord = Record<string, unknown>;

type WorkspaceReadReason =
  | "missing_workspace"
  | "permission_denied"
  | "invalid_authorization_response"
  | "invalid_response"
  | "server_enforcement_required"
  | "service_unavailable";

export class WorkspaceReadBlockedError extends Error {
  constructor(
    public readonly reason: WorkspaceReadReason,
    message: string,
  ) {
    super(message);
    this.name = "WorkspaceReadBlockedError";
  }
}

export interface VerifiedWorkspaceScope {
  labId: number;
}

export interface ClinicalPatientRead {
  id: string;
  display_name: string;
  birth_date?: string | null;
  gender?: string | null;
  created_at?: string | null;
}

export interface ClinicalOrderRead {
  id: string;
  patient_display_name?: string | null;
  practitioner_display_name?: string | null;
  status: string;
  test_count: number;
  created_at?: string | null;
}

interface ClinicalWorkspaceContext {
  organization_id: string;
  facility_id: string;
  workspace_id: string;
  department_id?: string | null;
}

interface ClinicalReadEnvelope<T> {
  contract_version: "1.0";
  request_id: string;
  correlation_id: string;
  workspace_context: ClinicalWorkspaceContext;
  items: T[];
  limit: number;
  next_cursor?: string | null;
  total?: number | null;
}

function asRecord(value: unknown): JsonRecord | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as JsonRecord)
    : null;
}

function asNonEmptyString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function asPositiveInteger(value: unknown): number | null {
  const numeric = typeof value === "number" ? value : Number(value);
  return Number.isInteger(numeric) && numeric > 0 ? numeric : null;
}

function rejectUnexpectedSensitiveKeys(record: JsonRecord, keys: string[]): void {
  if (keys.some((key) => Object.prototype.hasOwnProperty.call(record, key))) {
    throw new WorkspaceReadBlockedError(
      "invalid_response",
      "استجابة القراءة السريرية تحتوي على حقل غير مسموح به.",
    );
  }
}

export function parseVerifiedWorkspaceScope(payload: unknown): VerifiedWorkspaceScope {
  const root = asRecord(payload);
  const user = asRecord(root?.user);
  const labId = asPositiveInteger(user?.lab_id);

  if (!labId) {
    throw new WorkspaceReadBlockedError(
      "missing_workspace",
      "لا يتوفر سياق منشأة موثق لهذه الجلسة.",
    );
  }

  return { labId };
}

export function isPermissionGranted(payload: unknown): boolean {
  const record = asRecord(payload);
  return record?.allowed === true || record?.granted === true || record?.permitted === true || record?.decision === "allow";
}

function parseWorkspaceContext(value: unknown): ClinicalWorkspaceContext {
  const record = asRecord(value);
  const organizationId = asNonEmptyString(record?.organization_id);
  const facilityId = asNonEmptyString(record?.facility_id);
  const workspaceId = asNonEmptyString(record?.workspace_id);
  if (!organizationId || !facilityId || !workspaceId) {
    throw new WorkspaceReadBlockedError(
      "invalid_response",
      "استجابة القراءة السريرية لا تحتوي على سياق مساحة عمل موثق.",
    );
  }
  const departmentId = record?.department_id;
  if (departmentId !== undefined && departmentId !== null && typeof departmentId !== "string") {
    throw new WorkspaceReadBlockedError(
      "invalid_response",
      "سياق مساحة العمل في استجابة القراءة غير صالح.",
    );
  }
  return {
    organization_id: organizationId,
    facility_id: facilityId,
    workspace_id: workspaceId,
    department_id: departmentId as string | null | undefined,
  };
}

function parseEnvelope<T>(payload: unknown, parseItem: (item: unknown) => T): ClinicalReadEnvelope<T> {
  const root = asRecord(payload);
  if (root?.contract_version !== "1.0") {
    throw new WorkspaceReadBlockedError(
      "invalid_response",
      "إصدار عقد القراءة السريرية غير مدعوم.",
    );
  }
  const requestId = asNonEmptyString(root.request_id);
  const correlationId = asNonEmptyString(root.correlation_id);
  const items = root.items;
  const limit = asPositiveInteger(root.limit);
  if (!requestId || !correlationId || !Array.isArray(items) || !limit) {
    throw new WorkspaceReadBlockedError(
      "invalid_response",
      "استجابة القراءة السريرية غير مكتملة.",
    );
  }
  const total = root.total;
  if (total !== undefined && total !== null && (!Number.isInteger(total) || Number(total) < 0)) {
    throw new WorkspaceReadBlockedError(
      "invalid_response",
      "عدد نتائج القراءة السريرية غير صالح.",
    );
  }
  const nextCursor = root.next_cursor;
  if (nextCursor !== undefined && nextCursor !== null && typeof nextCursor !== "string") {
    throw new WorkspaceReadBlockedError(
      "invalid_response",
      "مؤشر الصفحة التالية في القراءة السريرية غير صالح.",
    );
  }
  return {
    contract_version: "1.0",
    request_id: requestId,
    correlation_id: correlationId,
    workspace_context: parseWorkspaceContext(root.workspace_context),
    items: items.map(parseItem),
    limit,
    next_cursor: nextCursor as string | null | undefined,
    total: total as number | null | undefined,
  };
}

export function parseClinicalPatientEnvelope(payload: unknown): ClinicalReadEnvelope<ClinicalPatientRead> {
  return parseEnvelope(payload, parsePatient);
}

export function parseClinicalOrderEnvelope(payload: unknown): ClinicalReadEnvelope<ClinicalOrderRead> {
  return parseEnvelope(payload, parseOrder);
}

function parsePatient(item: unknown): ClinicalPatientRead {
  const record = asRecord(item);
  if (!record) {
    throw new WorkspaceReadBlockedError("invalid_response", "سجل المريض في الاستجابة غير صالح.");
  }
  rejectUnexpectedSensitiveKeys(record, ["phone", "national_id", "national_id_hash", "lab_id"]);
  const id = asNonEmptyString(record.id);
  const displayName = asNonEmptyString(record.display_name);
  if (!id || !displayName) {
    throw new WorkspaceReadBlockedError("invalid_response", "سجل المريض في الاستجابة غير صالح.");
  }
  return {
    id,
    display_name: displayName,
    birth_date: record.birth_date as string | null | undefined,
    gender: record.gender as string | null | undefined,
    created_at: record.created_at as string | null | undefined,
  };
}

function parseOrder(item: unknown): ClinicalOrderRead {
  const record = asRecord(item);
  if (!record) {
    throw new WorkspaceReadBlockedError("invalid_response", "سجل الطلب في الاستجابة غير صالح.");
  }
  rejectUnexpectedSensitiveKeys(record, ["patient_id", "lab_id", "results"]);
  const id = asNonEmptyString(record.id);
  const status = asNonEmptyString(record.status);
  const testCount = record.test_count;
  if (!id || !status || !Number.isInteger(testCount) || Number(testCount) < 0) {
    throw new WorkspaceReadBlockedError("invalid_response", "سجل الطلب في الاستجابة غير صالح.");
  }
  return {
    id,
    patient_display_name: record.patient_display_name as string | null | undefined,
    practitioner_display_name: record.practitioner_display_name as string | null | undefined,
    status,
    test_count: Number(testCount),
    created_at: record.created_at as string | null | undefined,
  };
}

function mapGatewayError(error: unknown, contractId: string): WorkspaceReadBlockedError | null {
  if (!axios.isAxiosError(error)) return null;
  const status = error.response?.status;
  if (status === 401 || status === 403) {
    return new WorkspaceReadBlockedError(
      status === 401 ? "missing_workspace" : "permission_denied",
      `لا تملك جلسة أو صلاحية قراءة ${contractId} ضمن السياق الحالي.`,
    );
  }
  if (status === 503) {
    return new WorkspaceReadBlockedError(
      "service_unavailable",
      `بوابة القراءة ${contractId} غير مفعلة لهذا السياق أو غير متاحة حاليًا.`,
    );
  }
  return null;
}

export const workspaceScopedReads = {
  async listPatients(params?: { search?: string; cursor?: string; limit?: number }): Promise<ClinicalPatientRead[]> {
    try {
      const response = await api.get<unknown>(SCOPED_READ_CONTRACTS.patients.path, { params });
      const envelope = parseEnvelope(response.data, parsePatient);
      return envelope.items;
    } catch (error) {
      const mapped = mapGatewayError(error, SCOPED_READ_CONTRACTS.patients.id);
      throw mapped ?? error;
    }
  },

  async listOrders(params?: { search?: string; cursor?: string; limit?: number }): Promise<ClinicalOrderRead[]> {
    try {
      const response = await api.get<unknown>(SCOPED_READ_CONTRACTS.orders.path, { params });
      const envelope = parseEnvelope(response.data, parseOrder);
      return envelope.items;
    } catch (error) {
      const mapped = mapGatewayError(error, SCOPED_READ_CONTRACTS.orders.id);
      throw mapped ?? error;
    }
  },
};
