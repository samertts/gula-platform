import { describe, expect, it } from "vitest";
import { filterOrders, nextMobileSidebarState, type LabOrder } from "./lab-data";

const ordersFixture: LabOrder[] = [
  { id: "TEST-1", patient: "مريض اختبار", test: "فحص الغدة", physician: "طبيب اختبار", receivedAt: "وقت اختبار", status: "مكتمل", priority: "عادي" },
  { id: "TEST-2", patient: "مريض آخر", test: "فحص دم", physician: "طبيب اختبار", receivedAt: "وقت اختبار", status: "معلق", priority: "عاجل" },
  { id: "TEST-3", patient: "مريض ثالث", test: "فحص آخر", physician: "طبيب ثالث", receivedAt: "وقت اختبار", status: "معلق", priority: "عادي" },
];

describe("filterOrders", () => {
  it("يعرض الطلبات المطابقة لعبارة البحث", () => {
    expect(filterOrders(ordersFixture, "الغدة", "الكل")).toHaveLength(1);
    expect(filterOrders(ordersFixture, "الغدة", "الكل")[0]?.id).toBe("TEST-1");
  });

  it("يطبق فلترة حالة الطلب من دون تغيير بيانات الاختبار المصدرية", () => {
    const pending = filterOrders(ordersFixture, "", "معلق");
    expect(pending).toHaveLength(2);
    expect(pending.every((item) => item.status === "معلق")).toBe(true);
    expect(ordersFixture).toHaveLength(3);
  });
});

describe("nextMobileSidebarState", () => {
  it("يفتح ويغلق القائمة الجانبية على الهاتف", () => {
    expect(nextMobileSidebarState(false)).toBe(true);
    expect(nextMobileSidebarState(true)).toBe(false);
  });
});
