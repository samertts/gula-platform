import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkspaceSelector } from "./WorkspaceSelector";
import { useAuth } from "@/contexts/AuthContext";
import type { WorkspaceSummary } from "@/api/client";

vi.mock("react-i18next", () => ({ useTranslation: () => ({ t: (_key: string, fallback: string) => fallback }) }));
vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));

const workspaceOne: WorkspaceSummary = { id: "workspace-1", uuid: "workspace-uuid-1", workspace_type: "citizen", name: "Citizen Workspace", name_ar: "مساحة المواطن", status: "active", organization_id: null, facility_id: null, department_id: null, professional_type: null, is_personal: true };
const workspaceTwo: WorkspaceSummary = { ...workspaceOne, id: "workspace-2", uuid: "workspace-uuid-2", workspace_type: "professional", name: "Professional Workspace", name_ar: "المساحة المهنية", professional_type: "physician", is_personal: false };

function setAuthMode(demoMode: boolean, overrides: Partial<ReturnType<typeof useAuth>> = {}) {
  vi.mocked(useAuth).mockReturnValue({
    demoMode,
    state: demoMode ? "AUTHENTICATED" : "AUTHORIZED",
    availableWorkspaces: [],
    memberships: [],
    workspace: null,
    error: null,
    switchWorkspace: vi.fn(),
    refreshWorkspaces: vi.fn().mockResolvedValue([]),
    ...overrides,
  } as ReturnType<typeof useAuth>);
}

beforeEach(() => { vi.clearAllMocks(); setAuthMode(false); });

describe("WorkspaceSelector", () => {
  it("shows a loading status while auth context discovery is pending", () => {
    setAuthMode(false, { state: "LOADING" });
    render(<WorkspaceSelector />);
    expect(screen.getByRole("status")).toHaveTextContent("جارٍ تحميل المساحات");
  });

  it("renders server workspaces without inferring an active context", async () => {
    const onActiveWorkspace = vi.fn();
    setAuthMode(false, { availableWorkspaces: [workspaceOne, workspaceTwo] });
    render(<WorkspaceSelector onActiveWorkspace={onActiveWorkspace} />);
    const selector = await screen.findByRole("combobox", { name: "اختيار مساحة العمل" });
    expect(selector).toHaveValue("");
    expect(screen.getByRole("option", { name: "مساحة المواطن" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "المساحة المهنية" })).toBeInTheDocument();
    expect(onActiveWorkspace).not.toHaveBeenCalled();
  });

  it("renders a safe empty state when the server returns no eligible workspace", async () => {
    setAuthMode(false, { availableWorkspaces: [] });
    render(<WorkspaceSelector />);
    expect(await screen.findByRole("status")).toHaveTextContent("لا توجد مساحة عمل مصرح بها");
  });

  it("renders a non-sensitive error state when context discovery fails", async () => {
    setAuthMode(false, { error: { code: "OFFLINE", message: "تعذر تحميل مساحات العمل", retryable: true } });
    render(<WorkspaceSelector />);
    expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تحميل مساحات العمل");
  });

  it("uses the server response as the only source of active context after switching", async () => {
    const user = userEvent.setup();
    const onActiveWorkspace = vi.fn();
    const switchWorkspace = vi.fn().mockResolvedValue(workspaceTwo);
    setAuthMode(false, { availableWorkspaces: [workspaceOne, workspaceTwo], switchWorkspace });
    render(<WorkspaceSelector onActiveWorkspace={onActiveWorkspace} />);
    const selector = await screen.findByRole("combobox", { name: "اختيار مساحة العمل" });
    await user.selectOptions(selector, "workspace-2");
    await waitFor(() => expect(switchWorkspace).toHaveBeenCalledWith("workspace-2"));
    expect(onActiveWorkspace).toHaveBeenLastCalledWith(workspaceTwo);
  });

  it("keeps the existing context and reports denial when server switching fails", async () => {
    const switchWorkspace = vi.fn().mockRejectedValue(new Error("403"));
    setAuthMode(false, { availableWorkspaces: [workspaceOne, workspaceTwo], workspace: workspaceOne, switchWorkspace });
    render(<WorkspaceSelector />);
    const selector = await screen.findByRole("combobox", { name: "اختيار مساحة العمل" });
    fireEvent.change(selector, { target: { value: "workspace-2" } });
    expect(await screen.findByRole("alert")).toHaveTextContent("تعذر تبديل مساحة العمل");
    await waitFor(() => expect(selector).toHaveValue("workspace-1"));
  });

  it("does not call workspace APIs in demo mode", () => {
    setAuthMode(true);
    render(<WorkspaceSelector />);
    expect(screen.getByRole("status")).toHaveTextContent("غير متاحة في وضع المعاينة");
  });
});
