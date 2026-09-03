import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { workspaceScopedReads, WorkspaceReadBlockedError } from "@/api/workspaceScopedReads";
import { DoctorWorkspacePanel } from "./DoctorWorkspacePanel";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

vi.mock("@/api/client", () => ({
  apiClient: {
    listWorkspaces: vi.fn(),
    switchWorkspace: vi.fn(),
  },
}));

vi.mock("@/api/workspaceScopedReads", () => ({
  workspaceScopedReads: {
    listPatients: vi.fn(),
    listOrders: vi.fn(),
  },
  WorkspaceReadBlockedError: class WorkspaceReadBlockedError extends Error {},
}));

const physicianWorkspace = {
  id: "workspace-physician",
  uuid: "physician-uuid",
  workspace_type: "professional",
  name: "Physician Workspace",
  name_ar: "المساحة المهنية للطبيب",
  status: "ACTIVE",
  organization_id: "org-1",
  facility_id: "facility-1",
  department_id: "department-1",
  professional_type: "physician",
  is_personal: false,
};

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/dashboard"]}>
        <DoctorWorkspacePanel />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DoctorWorkspacePanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "طبيب تجريبي", email: "doctor@example.invalid", role: "doctor", is_verified: true },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [physicianWorkspace] });
    vi.mocked(apiClient.switchWorkspace).mockResolvedValue({
      context: { account_id: "account-1", identity_id: "identity-1", workspace_id: physicianWorkspace.id, version: 2 },
      workspace: physicianWorkspace,
    });
    vi.mocked(workspaceScopedReads.listPatients).mockResolvedValue([
      { id: "patient-1", display_name: "مريض ضمن النطاق", gender: "ذكر", created_at: "2026-08-27T08:00:00Z" },
    ]);
    vi.mocked(workspaceScopedReads.listOrders).mockResolvedValue([
      { id: "order-1", patient_display_name: "مريض ضمن النطاق", status: "released", test_count: 2, created_at: "2026-08-27T08:10:00Z" },
    ]);
  });

  it("يبقي العرض التجريبي اصطناعياً ولا يستدعي workspace أو clinical gateway", () => {
    renderPanel();

    expect(screen.getByRole("heading", { name: "مركز العمل السريري للطبيب" })).toBeInTheDocument();
    expect(screen.getByText("لا توجد بيانات حقيقية")).toBeInTheDocument();
    expect(screen.getAllByText("سارة عبد الرحمن · تجريبي").length).toBeGreaterThan(0);
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listPatients).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();
  });

  it("لا يفتح القراءة الحية قبل تفعيل مساحة مهنية، ثم يستخدم عقد الخادم فقط", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "طبيب حي", email: "doctor@example.invalid", role: "doctor", is_verified: true },
    } as ReturnType<typeof useAuth>);

    renderPanel();

    expect(await screen.findByText("المساحة المهنية للطبيب")).toBeInTheDocument();
    expect(workspaceScopedReads.listPatients).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "تفعيل السياق" }));

    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalledWith("workspace-physician"));
    await waitFor(() => expect(workspaceScopedReads.listPatients).toHaveBeenCalledWith({ limit: 10 }));
    await waitFor(() => expect(workspaceScopedReads.listOrders).toHaveBeenCalledWith({ limit: 10 }));
    expect(screen.getAllByText("مريض ضمن النطاق").length).toBeGreaterThan(0);
    expect(screen.queryByText("phone")).not.toBeInTheDocument();
  });

  it("يتوقف بأمان عند رفض clinical gateway ولا يستخدم fallback legacy", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "طبيب حي", email: "doctor@example.invalid", role: "doctor", is_verified: true },
    } as ReturnType<typeof useAuth>);
    const blocked = new WorkspaceReadBlockedError("permission_denied", "لا تملك صلاحية القراءة ضمن السياق الحالي.");
    vi.mocked(workspaceScopedReads.listPatients).mockRejectedValue(blocked);
    vi.mocked(workspaceScopedReads.listOrders).mockRejectedValue(blocked);

    renderPanel();
    fireEvent.click(await screen.findByRole("button", { name: "تفعيل السياق" }));

    await waitFor(() => expect(workspaceScopedReads.listPatients).toHaveBeenCalledTimes(1));
    expect(screen.getAllByText("القراءة موقوفة بأمان").length).toBeGreaterThan(0);
    expect(workspaceScopedReads.listPatients).toHaveBeenCalledTimes(1);
    expect(workspaceScopedReads.listOrders).toHaveBeenCalledTimes(1);
  });
});
