import { describe, expect, it } from "vitest";
import { EhrPage } from "./EhrPage";
import { LegacyRouteBridge } from "@/pages/migration/LegacyRouteBridge";

describe("صفحة السجل الصحي الإلكتروني", () => {
  it("تعرض الجسر الآمن بدل تنفيذ قراءات سريرية مباشرة", () => {
    const element = EhrPage();

    expect(element.type).toBe(LegacyRouteBridge);
  });
});
