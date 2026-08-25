import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { axe } from "vitest-axe";
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

describe("WorkspaceContextHeader accessibility", () => {
  it.each([
    ["demo", <WorkspaceContextHeader demoMode role="doctor" />],
    ["live-empty", <WorkspaceContextHeader demoMode={false} role="doctor" />],
    ["live-context", <WorkspaceContextHeader demoMode={false} role="admin" workspace={workspace} />],
  ])("has no axe violations in %s state", async (_state, element) => {
    const { container } = render(element);
    const results = await axe(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });
});
