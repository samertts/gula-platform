import { describe, expect, it } from "vitest";
import ar from "@/i18n/ar";
import { hasPermission, NAV_ITEMS } from ".";
import { getRouteRoles } from "./routePolicies";

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
      "/my-record",
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

  it("يطابق كل رابط محمي سياسة أدوار المسار المركزية", () => {
    const items = Object.values(NAV_ITEMS).flat();
    const guardedItems = items.filter((item) => item.roles);

    expect(guardedItems.length).toBeGreaterThan(0);
    for (const item of guardedItems) {
      expect(getRouteRoles(item.path), item.path).toBeDefined();
      expect([...item.roles!], item.path).toEqual([...getRouteRoles(item.path)!]);
    }
  });

  it("لا يعرض أسطح الإدارة والمستشفى للطبيب أو الفني", () => {
    const items = Object.values(NAV_ITEMS).flat();
    const visibleFor = (role: string) =>
      items.filter(
        (item) =>
          (!item.roles || item.roles.includes(role)) &&
          (!item.permissions || item.permissions.some((permission) => hasPermission(role, permission))),
      );

    const doctorPaths = visibleFor("doctor").map((item) => item.path);
    const technicianPaths = visibleFor("technician").map((item) => item.path);

    expect(doctorPaths).toEqual(expect.arrayContaining([
      "/dashboard",
      "/patient-management",
      "/orders",
      "/results",
    ]));
    expect(doctorPaths).not.toContain("/hospital");
    expect(doctorPaths).not.toContain("/admin");
    expect(technicianPaths).not.toContain("/hospital");
    expect(technicianPaths).not.toContain("/admin");
    expect(technicianPaths).not.toContain("/reports");
  });

  it("يقصر مركز ربط الأجهزة على صلاحية المختبر والحسابات المؤسسية", () => {
    const deviceItem = (NAV_ITEMS.systems ?? []).find((item) => item.path === "/device-integration");

    expect(deviceItem).toMatchObject({
      permissions: ["lab:read"],
      institutionalOnly: true,
    });
  });
});
