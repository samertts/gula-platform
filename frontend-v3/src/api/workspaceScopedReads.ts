import { api } from "@/api/client";
import type { LabOrder, Patient } from "@/types";

export const SCOPED_READ_CONTRACTS = {
  patients: {
    id: "patients.read",
    path: "/patients",
    permission: "patients:read",
  },
  orders: {
    id: "orders.read",
    path: "/lims/orders",
    permission: "orders:read",
  },
} as const;

/**
 * موجهات `/patients` و`/lims/orders` تعزل بـ `lab_id`، لكنها لا تستدعي
 * حارس صلاحية دقيقًا في الخادم. فحص `/authz/check` الذي يجريه المتصفح لا
 * يكفي وحده لإلزام القرار لأن أي عميل يمكنه تجاوز خطوة الواجهة وطلب القراءة
 * مباشرة. تبقى هذه القيمة ثابتة حتى يستهلك frontend-v3 جسرًا خادميًا موثقًا
 * أو يضاف الحارس الصريح إلى الموجهات التنفيذية.
 */
export const DIRECT_REST_SCOPED_READS_BLOCKED = true;

type JsonRecord = Record<string, unknown>;

export class WorkspaceReadBlockedError extends Error {
  constructor(
    public readonly reason:
      | "missing_workspace"
      | "permission_denied"
      | "invalid_authorization_response"
      | "server_enforcement_required",
    message: string,
  ) {
    super(message);
    this.name = "WorkspaceReadBlockedError";
  }
}

function requireServerEnforcedRead(contractId: string): never {
  throw new WorkspaceReadBlockedError(
    "server_enforcement_required",
    `أُوقفت قراءة ${contractId} لأن فرض الصلاحية الخادمي للعقد غير مثبت بعد.`,
  );
}

export interface VerifiedWorkspaceScope {
  labId: number;
}

function asRecord(value: unknown): JsonRecord | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as JsonRecord)
    : null;
}

function asPositiveInteger(value: unknown): number | null {
  const numeric = typeof value === "number" ? value : Number(value);
  return Number.isInteger(numeric) && numeric > 0 ? numeric : null;
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

async function requireVerifiedWorkspacePermission(permission: string): Promise<VerifiedWorkspaceScope> {
  const identityResponse = await api.get<unknown>("/authz/me");
  const scope = parseVerifiedWorkspaceScope(identityResponse.data);

  const permissionResponse = await api.post<unknown>("/authz/check", {
    permission,
    resource_attrs: { lab_id: scope.labId },
    environment: { client_surface: "frontend-v3" },
  });

  if (!isPermissionGranted(permissionResponse.data)) {
    throw new WorkspaceReadBlockedError(
      "permission_denied",
      "لا تملك الصلاحية اللازمة لقراءة بيانات هذه المنشأة.",
    );
  }

  return scope;
}

function extractList<T>(payload: unknown, keys: string[]): T[] {
  if (Array.isArray(payload)) return payload as T[];
  const record = asRecord(payload);
  for (const key of keys) {
    const candidate = record?.[key];
    if (Array.isArray(candidate)) return candidate as T[];
  }
  return [];
}

export const workspaceScopedReads = {
  async listPatients(params?: { search?: string; skip?: number; limit?: number }): Promise<Patient[]> {
    if (DIRECT_REST_SCOPED_READS_BLOCKED) {
      return requireServerEnforcedRead(SCOPED_READ_CONTRACTS.patients.id);
    }
    await requireVerifiedWorkspacePermission(SCOPED_READ_CONTRACTS.patients.permission);
    const response = await api.get<unknown>(SCOPED_READ_CONTRACTS.patients.path, { params });
    return extractList<Patient>(response.data, ["items", "patients", "data"]);
  },

  async listOrders(params?: { search?: string; skip?: number; limit?: number }): Promise<LabOrder[]> {
    if (DIRECT_REST_SCOPED_READS_BLOCKED) {
      return requireServerEnforcedRead(SCOPED_READ_CONTRACTS.orders.id);
    }
    await requireVerifiedWorkspacePermission(SCOPED_READ_CONTRACTS.orders.permission);
    const response = await api.get<unknown>(SCOPED_READ_CONTRACTS.orders.path, { params });
    return extractList<LabOrder>(response.data, ["items", "orders", "data"]);
  },
};
