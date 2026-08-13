import { describe, expect, it, vi } from "vitest";
import { apiClient, DEMO_PERSONAS } from "./client";
import { authApi, dashboardApi } from "./endpoints";

describe("العرض التجريبي المعزول", () => {
  it("ينشئ جلسات للشخصيات التجريبية دون إرسال طلب تسجيل دخول", async () => {
    const postSpy = vi.spyOn(apiClient.api, "post");

    try {
      for (const persona of DEMO_PERSONAS) {
        const session = await authApi.demoAccess(persona.id);
        expect(session).toMatchObject({
          demo_mode: true,
          demo_persona: persona.id,
          user: {
            id: `demo-${persona.id}`,
            role: persona.role,
            lab_id: "demo-tenant",
          },
        });
      }
      expect(postSpy).not.toHaveBeenCalled();
    } finally {
      postSpy.mockRestore();
    }
  });

  it("يعرض مؤشرات Demo الاصطناعية محلياً دون طلب لوحة تحكم من الخادم", async () => {
    const getSpy = vi.spyOn(apiClient.api, "get");

    try {
      const expected = {
        doctor: { total_patients: 24, today_orders: 11, today_results: 17, critical_alerts: 2 },
        technician: { total_patients: 12, today_orders: 18, today_results: 26, critical_alerts: 1 },
        lab_admin: { total_patients: 48, today_orders: 32, today_results: 39, critical_alerts: 4 },
        citizen: { total_patients: 1, today_orders: 2, today_results: 2, critical_alerts: 0 },
      } as const;

      for (const persona of DEMO_PERSONAS) {
        const dashboard = await dashboardApi.demo(persona.id);
        expect(dashboard).toMatchObject({ demo_mode: true, ...expected[persona.id] });
      }
      expect(getSpy).not.toHaveBeenCalled();
    } finally {
      getSpy.mockRestore();
    }
  });
});
