import { describe, expect, it } from "vitest";
import ar from "@/i18n/ar";
import { NAV_ITEMS } from ".";

describe("التنقل العربي الأساسي في GULA", () => {
  it("يحافظ على مسارات الرئيسية والطلبات والمرضى والتقارير والإعدادات", () => {
    const mainItems = NAV_ITEMS.main ?? [];
    const settingsItems = NAV_ITEMS.settings ?? [];
    const paths = [
      ...mainItems.map((item) => item.path),
      ...settingsItems.map((item) => item.path),
    ];

    expect(paths).toEqual(expect.arrayContaining([
      "/dashboard",
      "/orders",
      "/patients",
      "/reports",
      "/settings",
    ]));
  });

  it("يعرّف تسمية التقارير بالعربية في قاموس الملاحة", () => {
    expect(ar.nav.reports).toBe("التقارير");
  });

  it("لا يطلب سطح التقارير صلاحية تشغيلية غير موثقة", () => {
    const reportsItem = (NAV_ITEMS.main ?? []).find((item) => item.path === "/reports");

    expect(reportsItem).toMatchObject({
      label: "nav.reports",
      permissions: ["dashboard:read"],
    });
  });
});
