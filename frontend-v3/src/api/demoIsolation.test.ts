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
      const dashboard = await dashboardApi.demo();

      expect(dashboard).toMatchObject({
        demo_mode: true,
        total_patients: 15,
        today_orders: 8,
        today_results: 12,
        critical_alerts: 2,
      });
      expect(getSpy).not.toHaveBeenCalled();
    } finally {
      getSpy.mockRestore();
    }
  });
});
