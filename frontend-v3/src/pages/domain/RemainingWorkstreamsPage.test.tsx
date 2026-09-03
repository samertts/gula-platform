import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import RemainingWorkstreamsPage from "./RemainingWorkstreamsPage";

describe("RemainingWorkstreamsPage", () => {
  it("يعرض المهام الاثنتي عشرة وأسباب الحجب في الحالة الافتراضية", () => {
    render(<MemoryRouter><RemainingWorkstreamsPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "سجل المتبقي من المهام السابقة" })).toBeInTheDocument();
    expect(screen.getByText("0/12 مسارات مؤهلة للإعلان كمكتملة")).toBeInTheDocument();
    expect(screen.getByText("المواطن والهوية")).toBeInTheDocument();
    expect(screen.getByText("الطوارئ والإسعاف والرعاية الحادة")).toBeInTheDocument();
    expect(screen.getAllByText("سبب الحجب")).toHaveLength(12);
  });

  it("يتيح تصفية العناصر المحجوبة دون تغيير أي بيانات", () => {
    render(<MemoryRouter><RemainingWorkstreamsPage /></MemoryRouter>);

    fireEvent.click(screen.getByRole("button", { name: "المحجوب" }));

    expect(screen.getByText("المختبر")).toBeInTheDocument();
    expect(screen.getByText("الأشعة والتصوير")).toBeInTheDocument();
    expect(screen.queryByText("Unified Clinical Journey & Design System")).not.toBeInTheDocument();
  });
});
