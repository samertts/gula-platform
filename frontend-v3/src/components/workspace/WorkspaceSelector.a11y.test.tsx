import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import { WorkspaceSelector } from "./WorkspaceSelector";
import { apiClient } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (_key: string, fallback: string) => fallback }),
}));

vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));

vi.mock("@/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/api/client")>("@/api/client");
  return {
    ...actual,
    apiClient: {
      ...actual.apiClient,
      listWorkspaces: vi.fn(),
      switchWorkspace: vi.fn(),
    },
  };
});

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(useAuth).mockReturnValue({ demoMode: false } as ReturnType<typeof useAuth>);
  vi.mocked(apiClient.listWorkspaces).mockResolvedValue({
    workspaces: [
      {
        id: "workspace-1",
        uuid: "workspace-uuid-1",
        workspace_type: "citizen",
        name: "Citizen Workspace",
        name_ar: "مساحة المواطن",
        status: "active",
        organization_id: null,
        facility_id: null,
        department_id: null,
        professional_type: null,
        is_personal: true,
      },
    ],
  });
});

describe("WorkspaceSelector accessibility", () => {
  it("has no axe violations in the active workspace state", async () => {
    const { container } = render(<WorkspaceSelector />);
    await screen.findByRole("combobox", { name: "اختيار مساحة العمل" });

    const results = await axe(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });
});
