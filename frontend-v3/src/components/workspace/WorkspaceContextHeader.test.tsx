import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WorkspaceContextHeader } from "./WorkspaceContextHeader";

const workspace = {
  id: "workspace-1",
  uuid: "workspace-uuid-1",
  workspace_type: "clinic",
  name: "GULA Clinic",
  name_ar: "عيادة GULA",
  status: "active",
  organization_id: "org-1",
  facility_id: "facility-1",
  department_id: "department-1",
  professional_type: null,
  is_personal: false,
};

describe("WorkspaceContextHeader", () => {
  it("shows isolated synthetic context in demo without workspace data", () => {
    render(<WorkspaceContextHeader demoMode role="doctor" />);

    expect(screen.getByRole("region", { name: "سياق الوصول الحالي" })).toHaveTextContent(
      "مساحة GULA الاصطناعية المعزولة",
    );
    expect(screen.getByText("طبيب · قراءة فقط")).toBeInTheDocument();
    expect(screen.queryByText("عيادة GULA")).not.toBeInTheDocument();
  });

  it("fails closed when live workspace context is unavailable", () => {
    render(<WorkspaceContextHeader demoMode={false} role="doctor" />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "لم تُحمّل مساحة عمل مصرح بها",
    );
    expect(screen.queryByText("GULA Clinic")).not.toBeInTheDocument();
  });

  it("renders only server-returned workspace context in live mode", () => {
    render(<WorkspaceContextHeader demoMode={false} role="admin" workspace={workspace} />);

    expect(screen.getByRole("region", { name: "سياق الوصول الحالي" })).toHaveTextContent(
      "عيادة GULA",
    );
    expect(screen.getByText(/مدير مختبر/)).toBeInTheDocument();
    expect(screen.getByText(/الحالة: active/)).toBeInTheDocument();
  });
});
