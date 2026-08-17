import axios from "axios";
import { apiClient } from "./client";
import {
  DIRECT_REST_SCOPED_READS_BLOCKED,
  WorkspaceReadBlockedError,
  isPermissionGranted,
  parseClinicalOrderEnvelope,
  parseClinicalPatientEnvelope,
  parseClinicalResultEnvelope,
  parseVerifiedWorkspaceScope,
  workspaceScopedReads,
} from "./workspaceScopedReads";
import { describe, expect, it, vi } from "vitest";

describe("بوابة القراءة السريرية الموحدة", () => {
  const baseEnvelope = {
    contract_version: "1.0",
    request_id: "00000000-0000-4000-8000-000000000001",
    correlation_id: "00000000-0000-4000-8000-000000000002",
    workspace_context: {
      organization_id: "org-1",
      facility_id: "facility-1",
      workspace_id: "workspace-1",
      department_id: null,
    },
    limit: 50,
    total: 1,
    next_cursor: null,
  } as const;

  it("تُبقي REST القديم محجوبًا ولا تستخدم fallback صامتًا", () => {
    expect(DIRECT_REST_SCOPED_READS_BLOCKED).toBe(true);
  });

  it("تستخرج مختبرًا موثقًا من legacy auth payload فقط للتوافق القديم", () => {
    expect(parseVerifiedWorkspaceScope({ user: { lab_id: 24 } })).toEqual({ labId: 24 });
  });

  it("تقبل فقط نتيجة سماح صريحة من عقد التفويض القديم", () => {
    expect(isPermissionGranted({ allowed: true })).toBe(true);
    expect(isPermissionGranted({ decision: "deny" })).toBe(false);
    expect(isPermissionGranted({})).toBe(false);
  });

  it("تتحقق من عقد patients.read version 1.0 وسياق workspace", () => {
    expect(
      parseClinicalPatientEnvelope({
        ...baseEnvelope,
        items: [{ id: "7", display_name: "Ali Hassan", birth_date: "1990-01-01", gender: "M", created_at: "2026-01-01T00:00:00Z" }],
      }),
    ).toMatchObject({
      contract_version: "1.0",
      workspace_context: { organization_id: "org-1", facility_id: "facility-1", workspace_id: "workspace-1" },
      items: [{ id: "7", display_name: "Ali Hassan" }],
    });
  });

  it("ترفض response يحتوي حقول phone/lab_id الحساسة أو legacy", () => {
    expect(() =>
      parseClinicalPatientEnvelope({
        ...baseEnvelope,
        items: [{ id: "7", display_name: "Ali Hassan", phone: "+964700000000", lab_id: 21 }],
      }),
    ).toThrowError(WorkspaceReadBlockedError);
  });

  it("تستخدم فقط مسار gateway المسموح وتُرجع order DTO minimal", async () => {
    const getSpy = vi.spyOn(apiClient.api, "get").mockResolvedValueOnce({
      data: {
        ...baseEnvelope,
        items: [{ id: "order-7", patient_display_name: "Ali Hassan", practitioner_display_name: "Dr. Noor", status: "pending", test_count: 2, created_at: "2026-01-01T00:00:00Z" }],
      },
    } as never);

    await expect(workspaceScopedReads.listOrders({ limit: 50 })).resolves.toEqual([
      {
        id: "order-7",
        patient_display_name: "Ali Hassan",
        practitioner_display_name: "Dr. Noor",
        status: "pending",
        test_count: 2,
        created_at: "2026-01-01T00:00:00Z",
      },
    ]);
    expect(getSpy).toHaveBeenCalledWith("/api/v1/clinical/orders", { params: { limit: 50 } });
    getSpy.mockRestore();
  });

  it("تتحقق من عقد results.read وترفض حقول المشاركة العامة", async () => {
    expect(() =>
      parseClinicalResultEnvelope({
        ...baseEnvelope,
        items: [{ id: "result-1", order_id: "7", test_name: "Glucose", value: 5.2, unit: "mmol/L", result_token: "secret" }],
      }),
    ).toThrowError(WorkspaceReadBlockedError);

    const getSpy = vi.spyOn(apiClient.api, "get").mockResolvedValueOnce({
      data: {
        ...baseEnvelope,
        items: [{ id: "result-1", order_id: "7", test_name: "Glucose", value: 5.2, unit: "mmol/L", flag: "normal" }],
      },
    } as never);

    await expect(workspaceScopedReads.listResults("7")).resolves.toEqual([
      { id: "result-1", order_id: "7", test_name: "Glucose", value: 5.2, unit: "mmol/L", flag: "normal" },
    ]);
    expect(getSpy).toHaveBeenCalledWith("/api/v1/clinical/orders/7/results");
    getSpy.mockRestore();
  });

  it("ترفض contract_version غير المدعوم ولا تعود إلى legacy endpoint", () => {
    expect(() =>
      parseClinicalOrderEnvelope({
        ...baseEnvelope,
        contract_version: "0.9",
        items: [{ id: "order-7", status: "pending", test_count: 1 }],
      }),
    ).toThrowError(WorkspaceReadBlockedError);
  });

  it("تحول فشل الاتصال إلى حالة blocked آمنة بدل تسريب transport error", async () => {
    const getSpy = vi.spyOn(apiClient.api, "get").mockRejectedValueOnce(new axios.AxiosError("Network Error"));

    await expect(workspaceScopedReads.listPatients()).rejects.toMatchObject({
      name: "WorkspaceReadBlockedError",
      reason: "service_unavailable",
    });
    getSpy.mockRestore();
  });
});
