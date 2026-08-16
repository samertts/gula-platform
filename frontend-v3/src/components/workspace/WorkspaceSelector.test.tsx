import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkspaceSelector } from "./WorkspaceSelector";
import { apiClient, type WorkspaceSummary } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (_key: string, fallback: string) => fallback,
  }),
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

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

const workspaceOne: WorkspaceSummary = {
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
};

const workspaceTwo: WorkspaceSummary = {
  ...workspaceOne,
  id: "workspace-2",
  uuid: "workspace-uuid-2",
  workspace_type: "professional",
  name: "Professional Workspace",
  name_ar: "المساحة المهنية",
  professional_type: "physician",
  is_personal: false,
};

function setAuthMode(demoMode: boolean) {
  vi.mocked(useAuth).mockReturnValue({ demoMode } as ReturnType<typeof useAuth>);
}

beforeEach(() => {
  vi.clearAllMocks();
  setAuthMode(false);
});

describe("WorkspaceSelector", () => {
  it("shows a loading status while backend discovery is pending", () => {
    vi.mocked(apiClient.listWorkspaces).mockReturnValue(new Promise(() => undefined));

    render(<WorkspaceSelector />);

    expect(screen.getByRole("status")).toHaveTextContent("جارٍ تحميل المساحات");
  });

  it("renders server workspaces without inferring an active context", async () => {
    const onActiveWorkspace = vi.fn();
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [workspaceOne, workspaceTwo] });

    render(<WorkspaceSelector onActiveWorkspace={onActiveWorkspace} />);

    const selector = await screen.findByRole("combobox", { name: "اختيار مساحة العمل" });
    expect(selector).toHaveValue("");
    expect(screen.getByRole("option", { name: "مساحة المواطن" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "المساحة المهنية" })).toBeInTheDocument();
    expect(onActiveWorkspace).not.toHaveBeenCalled();
  });

  it("renders a safe empty state when the backend returns no eligible workspace", async () => {
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [] });

    render(<WorkspaceSelector />);

    expect(await screen.findByRole("status")).toHaveTextContent("لا توجد مساحة عمل مصرح بها");
  });

  it("renders a non-sensitive error state when discovery fails", async () => {
    vi.mocked(apiClient.listWorkspaces).mockRejectedValue(new Error("401"));

    render(<WorkspaceSelector />);

    expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تحميل مساحات العمل");
  });

  it("uses the server response as the only source of active context after switching", async () => {
    const user = userEvent.setup();
    const onActiveWorkspace = vi.fn();
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [workspaceOne, workspaceTwo] });
    vi.mocked(apiClient.switchWorkspace).mockResolvedValue({
      context: {
        account_id: "account-1",
        identity_id: "identity-1",
        workspace_id: "workspace-2",
        version: 2,
      },
      workspace: workspaceTwo,
    });

    render(<WorkspaceSelector onActiveWorkspace={onActiveWorkspace} />);

    const selector = await screen.findByRole("combobox", { name: "اختيار مساحة العمل" });
    await user.selectOptions(selector, "workspace-2");

    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalledWith("workspace-2"));
    await waitFor(() => expect(selector).toHaveValue("workspace-2"));
    expect(onActiveWorkspace).toHaveBeenLastCalledWith(workspaceTwo);
  });

  it("keeps the existing context and reports denial when server switching fails", async () => {
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [workspaceOne, workspaceTwo] });
    vi.mocked(apiClient.switchWorkspace).mockRejectedValue(new Error("403"));

    render(<WorkspaceSelector />);

    const selector = await screen.findByRole("combobox", { name: "اختيار مساحة العمل" });
    fireEvent.change(selector, { target: { value: "workspace-2" } });

    expect(await screen.findByRole("alert")).toHaveTextContent("رفض الخادم تبديل مساحة العمل");
    expect(selector).toHaveValue("");
  });

  it("does not call operational workspace APIs in demo mode", () => {
    setAuthMode(true);

    render(<WorkspaceSelector />);

    expect(screen.getByRole("status")).toHaveTextContent("غير متاحة في وضع المعاينة");
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
  });
});
