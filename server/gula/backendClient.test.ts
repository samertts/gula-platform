import { describe, expect, it } from "vitest";
import {
  GULA_AUTHORIZATION_CONTEXT_CONTRACT,
  getGulaConnectionStatus,
  verifyGulaAuthorizationContext,
} from "./backendClient";

describe("طبقة تكييف خلفية GULA", () => {
  it("لا تحاول الاتصال عند غياب الإعداد الخادمي", async () => {
    const status = getGulaConnectionStatus({});
    const result = await verifyGulaAuthorizationContext({}, async () => {
      throw new Error("يجب ألا يُستدعى fetch دون إعداد");
    });

    expect(status.state).toBe("not_configured");
    expect(status.verificationAvailable).toBe(false);
    expect(result.state).toBe("not_configured");
  });

  it("يرسل رمز الخدمة من الخادم فقط إلى مسار العقد المسجل", async () => {
    let capturedUrl = "";
    let capturedHeaders: HeadersInit | undefined;

    const result = await verifyGulaAuthorizationContext(
      {
        GULA_BACKEND_BASE_URL: "https://api.example.test/",
        GULA_BACKEND_SERVICE_TOKEN: "service-token",
      },
      async (input, init) => {
        capturedUrl = input;
        capturedHeaders = init.headers;
        return { ok: true, status: 200 };
      },
    );

    expect(capturedUrl).toBe("https://api.example.test/authz/me");
    expect(capturedHeaders).toMatchObject({ Authorization: "Bearer service-token" });
    expect(result).toMatchObject({
      state: "verified",
      contractId: GULA_AUTHORIZATION_CONTEXT_CONTRACT.id,
    });
  });

  it("لا يكشف محتوى استجابة الخلفية عند فشل التحقق", async () => {
    const result = await verifyGulaAuthorizationContext(
      {
        GULA_BACKEND_BASE_URL: "https://api.example.test",
        GULA_BACKEND_SERVICE_TOKEN: "service-token",
      },
      async () => ({ ok: false, status: 403 }),
    );

    expect(result).toEqual({
      state: "unavailable",
      label: "تعذر التحقق من عقد الخلفية",
      description: "رفضت خدمة الخلفية طلب التحقق أو لم تكن متاحة. لم تُعرض أي بيانات من الاستجابة.",
      contractId: "authorization.context.read",
      statusCode: 403,
    });
  });
});
