import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

function createContext(role: "user" | "admin"): TrpcContext {
  return {
    user: {
      id: role === "admin" ? 2 : 1,
      openId: `${role}-user`,
      email: `${role}@example.com`,
      name: role,
      loginMethod: "manus",
      role,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

describe("integration.verifyAuthorizationContext", () => {
  it("يرفض المستخدم غير الإداري قبل أي محاولة تحقق خادمي", async () => {
    const caller = appRouter.createCaller(createContext("user"));

    await expect(caller.integration.verifyAuthorizationContext()).rejects.toMatchObject({
      code: "FORBIDDEN",
    });
  });

  it("يعرض للإداري حالة غير معدة آمنة عند غياب اعتماد الخلفية", async () => {
    const caller = appRouter.createCaller(createContext("admin"));

    await expect(caller.integration.verifyAuthorizationContext()).resolves.toMatchObject({
      state: "not_configured",
      contractId: "authorization.context.read",
    });
  });
});
