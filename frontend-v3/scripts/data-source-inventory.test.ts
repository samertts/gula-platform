import { describe, expect, it } from "vitest";
import { buildDataSourceInventory } from "./data-source-inventory.mjs";

describe("جرد مصادر بيانات frontend-v3", () => {
  it("يصنف كل سطح مكتشف إلى حالة حوكمة مسموحة ويحتفظ بالأسطح السريرية الحساسة", async () => {
    const inventory = await buildDataSourceInventory();

    expect(inventory.surfaces.length).toBeGreaterThan(0);
    expect(inventory.surfaces.every((surface) => inventory.allowedClassifications.includes(surface.classification))).toBe(true);

    expect(inventory.surfaces).toEqual(expect.arrayContaining([
      expect.objectContaining({ source: "src/pages/patients/PatientsPage.tsx", classification: "contract-bound" }),
      expect.objectContaining({ source: "src/pages/orders/OrdersPage.tsx", classification: "contract-bound" }),
      expect.objectContaining({ source: "src/pages/ehr/EhrPage.tsx", classification: "safe_bridge" }),
      expect.objectContaining({ source: "src/pages/results/ResultsPage.tsx", classification: "safe_bridge" }),
      expect.objectContaining({ source: "src/pages/samples/SamplesPage.tsx", classification: "safe_bridge" }),
    ]));
  });

  it("يعزل كل سطح يعلن وضع demo بوصفه عرضًا تجريبيًا لا تشغيليًا", async () => {
    const inventory = await buildDataSourceInventory();
    const demoSurfaces = inventory.surfaces.filter((surface) => surface.kinds.includes("demo-surface"));

    expect(demoSurfaces.length).toBeGreaterThan(0);
    expect(demoSurfaces.every((surface) => surface.classification === "demo-only")).toBe(true);
  });
});
