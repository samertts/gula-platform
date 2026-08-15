import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PatientVisitReadinessPage } from "./PatientVisitReadinessPage";

describe("PatientVisitReadinessPage", () => {
  it("renders the non-operational prototype boundary and readiness statuses", () => {
    render(<PatientVisitReadinessPage />);

    expect(screen.getByRole("heading", { name: "جاهزية نظام زيارة المريض" })).toBeInTheDocument();
    expect(screen.getByText("Prototype آمن وغير تشغيلي")).toBeInTheDocument();
    expect(screen.getAllByText("يعتمد على Backend").length).toBeGreaterThan(0);
    expect(screen.getAllByText("محجوب حاليًا").length).toBeGreaterThan(0);
    expect(screen.getByText(/لا توجد بيانات مرضى أو API/)).toBeInTheDocument();
  });
});
