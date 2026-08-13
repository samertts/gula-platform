import { getGulaConnectionStatus } from "./backendClient";
import type { VerifiedWorkspaceContext } from "./workspaceContext";

type Environment = Record<string, string | undefined>;
type JsonResponse = { ok: boolean; status: number; json?: () => Promise<unknown> };
type Fetcher = (input: string, init: RequestInit) => Promise<JsonResponse>;
type UnknownRecord = Record<string, unknown>;

export const GULA_PATIENTS_READ_CONTRACT = {
  id: "patients.read",
  method: "GET",
  path: "/patients",
  permission: "patients:read",
  requiresWorkspaceContext: true,
} as const;

export const GULA_ORDERS_READ_CONTRACT = {
  id: "orders.read",
  method: "GET",
  path: "/lims/orders",
  permission: "orders:read",
  requiresWorkspaceContext: true,
} as const;

type ScopedContract = typeof GULA_PATIENTS_READ_CONTRACT | typeof GULA_ORDERS_READ_CONTRACT;
type ScopedState = "not_configured" | "configuration_invalid" | "workspace_mismatch" | "permission_denied" | "unavailable" | "ready";

export type ScopedReadResult<T> = {
  state: ScopedState;
  label: string;
  description: string;
  contractId: ScopedContract["id"];
  requiredPermission: string;
  items?: T[];
  total?: number;
};

export type PatientListItem = {
  id: number;
  fullName: string;
  healthId: string | null;
  createdAt: string | null;
};

export type OrderListItem = {
  id: number;
  accessionNumber: string | null;
  status: string | null;
  priority: string | null;
  createdAt: string | null;
};

function configuredBaseUrl(env: Environment): string | null {
  const rawUrl = env.GULA_BACKEND_BASE_URL?.trim();
  if (!rawUrl) return null;
  try {
    const url = new URL(rawUrl);
    if (url.protocol !== "http:" && url.protocol !== "https:") return null;
    return url.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}

function asRecord(value: unknown): UnknownRecord | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as UnknownRecord) : null;
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function baseResult<T>(state: ScopedState, contract: ScopedContract, label: string, description: string): ScopedReadResult<T> {
  return { state, label, description, contractId: contract.id, requiredPermission: contract.permission };
}

function safeItems(value: unknown): UnknownRecord[] {
  return Array.isArray(value) ? value.map(asRecord).filter((item): item is UnknownRecord => Boolean(item)) : [];
}

function getPermissionSet(payload: unknown): Set<string> {
  const record = asRecord(payload);
  const permissions = record?.permissions;
  return new Set(Array.isArray(permissions) ? permissions.filter((item): item is string => typeof item === "string") : []);
}

async function readJson(response: JsonResponse): Promise<unknown | null> {
  if (!response.json) return null;
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function authorizeScopedRead<T>(
  contract: ScopedContract,
  workspace: VerifiedWorkspaceContext,
  env: Environment,
  fetcher: Fetcher,
): Promise<{ ok: true; baseUrl: string; token: string } | { ok: false; result: ScopedReadResult<T> }> {
  const connection = getGulaConnectionStatus(env);
  if (connection.state !== "ready") {
    return { ok: false, result: baseResult(connection.state, contract, connection.label, connection.description) };
  }

  const baseUrl = configuredBaseUrl(env);
  const token = env.GULA_BACKEND_SERVICE_TOKEN?.trim();
  if (!baseUrl || !token) {
    return {
      ok: false,
      result: baseResult("not_configured", contract, "الاتصال الخادمي غير مُعدّ", "لم يُنفذ أي طلب نطاقي لغياب إعداد خادمي مكتمل."),
    };
  }

  const headers = { Authorization: `Bearer ${token}`, Accept: "application/json" };
  try {
    const identityResponse = await fetcher(`${baseUrl}/authz/me`, { method: "GET", headers });
    const identity = identityResponse.ok ? asRecord(await readJson(identityResponse)) : null;
    const user = identity ? asRecord(identity.user) : null;
    const facility = identity ? asRecord(identity.facility) : null;
    const backendSubjectId = asNumber(user?.id);
    const backendLabId = asNumber(user?.lab_id);
    const backendFacilityId = asNumber(facility?.id);

    const identityMatches = backendSubjectId === workspace.gulaSubjectId && backendLabId === workspace.labId;
    const facilityMatches = workspace.facilityId === null || backendFacilityId === workspace.facilityId;
    if (!identityMatches || !facilityMatches) {
      return {
        ok: false,
        result: baseResult("workspace_mismatch", contract, "تعذر إثبات سياق المنشأة", "لا تطابق هوية أو مختبر أو منشأة خلفية الربط الخادمي الموثق؛ لم يُنفذ طلب البيانات."),
      };
    }

    const permissionsResponse = await fetcher(`${baseUrl}/authz/me/permissions`, { method: "GET", headers });
    const permissions = permissionsResponse.ok ? getPermissionSet(await readJson(permissionsResponse)) : new Set<string>();
    if (!permissions.has(contract.permission)) {
      return {
        ok: false,
        result: baseResult("permission_denied", contract, "الصلاحية الخلفية غير متاحة", "لم تثبت الخلفية صلاحية القراءة المطلوبة؛ لم يُنفذ طلب البيانات."),
      };
    }

    return { ok: true, baseUrl, token };
  } catch {
    return {
      ok: false,
      result: baseResult("unavailable", contract, "تعذر التحقق من التفويض", "لم يكتمل التحقق من هوية الخلفية وصلاحيتها؛ لم يُنفذ طلب البيانات."),
    };
  }
}

export async function readScopedPatients(
  workspace: VerifiedWorkspaceContext,
  input: { search?: string; skip: number; limit: number },
  env: Environment = process.env,
  fetcher: Fetcher = (input, init) => fetch(input, init),
): Promise<ScopedReadResult<PatientListItem>> {
  const authorization = await authorizeScopedRead<PatientListItem>(GULA_PATIENTS_READ_CONTRACT, workspace, env, fetcher);
  if (!authorization.ok) return authorization.result;

  const params = new URLSearchParams({ skip: String(input.skip), limit: String(input.limit) });
  if (input.search?.trim()) params.set("search", input.search.trim());
  try {
    const response = await fetcher(`${authorization.baseUrl}${GULA_PATIENTS_READ_CONTRACT.path}?${params}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${authorization.token}`, Accept: "application/json" },
    });
    const payload = response.ok ? asRecord(await readJson(response)) : null;
    if (!payload) return baseResult("unavailable", GULA_PATIENTS_READ_CONTRACT, "تعذر تحميل المرضى", "لم تُعرض أي بيانات لأن عقد الخلفية لم يعد استجابة قائمة صالحة.");

    const items = safeItems(payload.patients).flatMap((patient) => {
      const id = asNumber(patient.id);
      const fullName = asString(patient.full_name);
      return id !== null && fullName !== null ? [{ id, fullName, healthId: asString(patient.health_id), createdAt: asString(patient.created_at) }] : [];
    });
    return { state: "ready", label: "سجل المرضى متاح", description: "أعيدت حقول العرض الدنيا بعد تحقق الخادم من السياق والصلاحية.", contractId: GULA_PATIENTS_READ_CONTRACT.id, requiredPermission: GULA_PATIENTS_READ_CONTRACT.permission, items, total: asNumber(payload.total) ?? items.length };
  } catch {
    return baseResult("unavailable", GULA_PATIENTS_READ_CONTRACT, "تعذر تحميل المرضى", "لم يكتمل الاتصال بعقد المرضى؛ لم تُعرض أي بيانات.");
  }
}

export async function readScopedOrders(
  workspace: VerifiedWorkspaceContext,
  input: { status?: string; skip: number; limit: number },
  env: Environment = process.env,
  fetcher: Fetcher = (input, init) => fetch(input, init),
): Promise<ScopedReadResult<OrderListItem>> {
  const authorization = await authorizeScopedRead<OrderListItem>(GULA_ORDERS_READ_CONTRACT, workspace, env, fetcher);
  if (!authorization.ok) return authorization.result;

  const params = new URLSearchParams({ skip: String(input.skip), limit: String(input.limit) });
  if (input.status) params.set("status", input.status);
  try {
    const response = await fetcher(`${authorization.baseUrl}${GULA_ORDERS_READ_CONTRACT.path}?${params}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${authorization.token}`, Accept: "application/json" },
    });
    const payload = response.ok ? asRecord(await readJson(response)) : null;
    if (!payload) return baseResult("unavailable", GULA_ORDERS_READ_CONTRACT, "تعذر تحميل الطلبات", "لم تُعرض أي بيانات لأن عقد الخلفية لم يعد استجابة قائمة صالحة.");

    const items = safeItems(payload.orders).flatMap((order) => {
      const id = asNumber(order.id);
      return id !== null ? [{ id, accessionNumber: asString(order.accession_number), status: asString(order.order_status), priority: asString(order.priority), createdAt: asString(order.created_at) }] : [];
    });
    return { state: "ready", label: "قائمة الطلبات متاحة", description: "أعيدت حقول العرض الدنيا بعد تحقق الخادم من السياق والصلاحية.", contractId: GULA_ORDERS_READ_CONTRACT.id, requiredPermission: GULA_ORDERS_READ_CONTRACT.permission, items, total: asNumber(payload.total) ?? items.length };
  } catch {
    return baseResult("unavailable", GULA_ORDERS_READ_CONTRACT, "تعذر تحميل الطلبات", "لم يكتمل الاتصال بعقد الطلبات؛ لم تُعرض أي بيانات.");
  }
}
