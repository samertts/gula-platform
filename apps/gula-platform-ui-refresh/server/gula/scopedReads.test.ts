import { describe, expect, it } from "vitest";
import { readScopedOrders, readScopedPatients } from "./scopedReads";

const workspace = {
  gulaSubjectId: 41,
  labId: 12,
  organizationId: 8,
  facilityId: 5,
  assignmentRoleId: "lab-analyst",
  verifiedAt: new Date("2026-08-12T00:00:00.000Z"),
};

const env = {
  GULA_BACKEND_BASE_URL: "https://backend.example.test",
  GULA_BACKEND_SERVICE_TOKEN: "server-only-token",
};

describe("القراءات النطاقية في GULA", () => {
  it("لا ينفذ أي طلب عند غياب الإعداد الخادمي", async () => {
    let calls = 0;
    const result = await readScopedPatients(workspace, { skip: 0, limit: 25 }, {}, async () => {
      calls += 1;
      return { ok: true, status: 200, json: async () => ({}) };
    });

    expect(result.state).toBe("not_configured");
    expect(calls).toBe(0);
  });

  it("يرفض قراءة الطلبات قبل استدعاء البيانات عند غياب الصلاحية الخلفية", async () => {
    const paths: string[] = [];
    const result = await readScopedOrders(workspace, { skip: 0, limit: 25 }, env, async (input) => {
      paths.push(input);
      if (input.endsWith("/authz/me")) {
        return { ok: true, status: 200, json: async () => ({ user: { id: 41, lab_id: 12 }, facility: { id: 5 } }) };
      }
      return { ok: true, status: 200, json: async () => ({ permissions: ["patients:read"] }) };
    });

    expect(result.state).toBe("permission_denied");
    expect(paths).toEqual(["https://backend.example.test/authz/me", "https://backend.example.test/authz/me/permissions"]);
  });

  it("يعيد حقول الطلب الدنيا فقط بعد تطابق السياق والصلاحية", async () => {
    const result = await readScopedOrders(workspace, { skip: 0, limit: 25 }, env, async (input) => {
      if (input.endsWith("/authz/me")) {
        return { ok: true, status: 200, json: async () => ({ user: { id: 41, lab_id: 12 }, facility: { id: 5 } }) };
      }
      if (input.endsWith("/authz/me/permissions")) {
        return { ok: true, status: 200, json: async () => ({ permissions: ["orders:read"] }) };
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({
          total: 1,
          orders: [{ id: 91, accession_number: "A-0091", order_status: "pending", priority: "routine", created_at: "2026-08-10T12:00:00Z", patient_name: "لا يجب إعادته" }],
        }),
      };
    });

    expect(result).toMatchObject({ state: "ready", contractId: "orders.read", requiredPermission: "orders:read", total: 1 });
    expect(result.items).toEqual([{ id: 91, accessionNumber: "A-0091", status: "pending", priority: "routine", createdAt: "2026-08-10T12:00:00Z" }]);
  });
});
