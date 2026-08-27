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

  it("يقصر عمليات المختبر على أدوار المختبر وDemo", () => {
    expect(getRouteRoles("/lab-operations")).toEqual(expect.arrayContaining(["lab_admin", "lab_staff", "demo_viewer"]));
    expect(getRouteRoles("/lab-operations")).not.toContain("citizen");
    expect(getRouteRoles("/lab-operations")).not.toContain("doctor");
  });

  it("يقصر عمليات الصيدلية على أدوار الصيدلية وDemo", () => {
    expect(getRouteRoles("/pharmacy-operations")).toEqual(expect.arrayContaining(["staff", "cashier", "demo_viewer"]));
    expect(getRouteRoles("/pharmacy-operations")).not.toContain("citizen");
    expect(getRouteRoles("/pharmacy-operations")).not.toContain("doctor");
  });

  it("يقصر عمليات الأشعة على الأدوار السريرية والتشغيلية وDemo", () => {
    expect(getRouteRoles("/radiology-operations")).toEqual(expect.arrayContaining(["doctor", "staff", "technician", "demo_viewer"]));
    expect(getRouteRoles("/radiology-operations")).not.toContain("citizen");
  });

  it("يحمي بوابة المؤسسة الصحية بنطاق أدوار مؤسسية مستقل", () => {
    const items = Object.values(NAV_ITEMS).flat();
    const organizationItem = items.find((item) => item.path === "/organization-workspace");
    expect(organizationItem).toMatchObject({
      label: "بوابة المؤسسة الصحية",
      permissions: ["dashboard:read"],
    });
    expect(getRouteRoles("/organization-workspace")).toEqual(expect.arrayContaining(["doctor", "admin", "technician"]));
    expect(getRouteRoles("/organization-workspace")).not.toContain("citizen");
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
