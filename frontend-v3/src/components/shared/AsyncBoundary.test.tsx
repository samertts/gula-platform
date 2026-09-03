import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AsyncBoundary } from "./AsyncBoundary";

describe("AsyncBoundary clinical states", () => {
  it("يعرض حالة forbidden الموحدة بدلاً من المحتوى", () => {
    render(
      <AsyncBoundary
        isLoading={false}
        isError={false}
        clinicalState="forbidden"
        stateTitle="الوصول محجوب"
        stateDescription="لا يوجد سياق خادمي صالح."
      >
        <p>محتوى لا يجب عرضه</p>
      </AsyncBoundary>,
    );

    expect(screen.getByRole("alert", { name: "الوصول محجوب" })).toBeInTheDocument();
    expect(screen.queryByText("محتوى لا يجب عرضه")).not.toBeInTheDocument();
  });

  it("يعرض action قابل لإعادة المحاولة للحالات القابلة للاسترداد", () => {
    const onRetry = vi.fn();
    render(
      <AsyncBoundary
        isLoading={false}
        isError={false}
        clinicalState="offline"
        stateActionLabel="إعادة الاتصال"
        onRetry={onRetry}
      >
        <p>محتوى غير ظاهر</p>
      </AsyncBoundary>,
    );

    expect(screen.getByRole("button", { name: "إعادة الاتصال" })).toBeInTheDocument();
  });

  it("يبقي children عند الحالة loaded", () => {
    render(
      <AsyncBoundary isLoading={false} isError={false} clinicalState="loaded">
        <p>بيانات ضمن السياق</p>
      </AsyncBoundary>,
    );

    expect(screen.getByText("بيانات ضمن السياق")).toBeInTheDocument();
  });
});
