import { describe, expect, it } from "vitest";
import { resolveLegacyRoute } from "./LegacyRouteBridge";
import { frontendSurfaceCatalog } from "./frontendSurfaceCatalog";

describe("جسر المسارات الانتقالية", () => {
  it("يحوّل مدخل التطبيق التخصصي حين يوجد مكافئ v3 مثبت", () => {
    expect(resolveLegacyRoute("/pharmacy")).toMatchObject({ target: "/pharmacy" });
    expect(resolveLegacyRoute("/laboratory")).toMatchObject({ target: "/dashboard" });
    expect(resolveLegacyRoute("/ministry")).toMatchObject({ target: "/national-data" });
  });

  it("لا يوجّه تدفقًا سريريًا فرعيًا إلى مكافئ غير مثبت", () => {
    const rule = resolveLegacyRoute("/radiology/worklist");

    expect(rule).toMatchObject({ title: "مساحة الأشعة" });
    expect(rule).not.toHaveProperty("target");
  });

  it("يحافظ على تحويلات frontend-v2 المثبتة", () => {
    expect(resolveLegacyRoute("/lab/queue")).toMatchObject({ target: "/orders" });
  });

  it("يسجل كل مصدر واجهة أمامية معروف وحالة انتقاله", () => {
    expect(frontendSurfaceCatalog.map((surface) => surface.sourcePath)).toEqual([
      "frontend-v2",
      "apps/gula-web-suite",
      "platform/apps/citizen",
      "platform/apps/doctor",
      "platform/apps/hospital",
      "platform/apps/laboratory",
      "platform/apps/ministry",
      "platform/apps/nurse",
      "platform/apps/pharmacy",
      "platform/apps/radiology",
    ]);
    expect(frontendSurfaceCatalog.find((surface) => surface.id === "doctor")).toMatchObject({ status: "pending_contract" });
  });
});
