import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/api/client";
import { workspaceScopedReads } from "@/api/workspaceScopedReads";
import { useAuth } from "@/contexts/AuthContext";
import AcuteCareOperationsWorkspacePage from "./AcuteCareOperationsWorkspacePage";

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
}));

const acuteWorkspace = {
  id: "workspace-acute-1",
  uuid: "workspace-acute-1-uuid",
  workspace_type: "hospital",
  name: "Rafidain Acute Care",
  name_ar: "رعاية الرافدين الحادة",
  status: "ACTIVE",
  organization_id: "org-acute-1",
  facility_id: "facility-acute-1",
  department_id: "department-emergency-1",
  professional_type: "physician",
  is_personal: false,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/acute-care-operations"]}>
        <AcuteCareOperationsWorkspacePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AcuteCareOperationsWorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "زائر تجريبي", email: "demo@example.invalid", role: "demo_viewer" },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [acuteWorkspace] });
    vi.mocked(apiClient.switchWorkspace).mockResolvedValue({
      context: { account_id: "account-acute-1", identity_id: "identity-acute-1", workspace_id: acuteWorkspace.id, version: 2 },
      workspace: acuteWorkspace,
    });
    vi.mocked(workspaceScopedReads.listPatients).mockResolvedValue([
      { id: "patient-acute-1", display_name: "مريض رعاية حادة ضمن النطاق", birth_date: null, gender: null, created_at: null },
    ]);
    vi.mocked(workspaceScopedReads.listOrders).mockResolvedValue([
      { id: "order-acute-1", patient_display_name: "مريض رعاية حادة ضمن النطاق", practitioner_display_name: "طبيب طوارئ ضمن السياق", status: "active", test_count: 2, created_at: null },
    ]);
  });

  it("يعرض رحلة الطوارئ والإسعاف الاصطناعية دون API حي أو كتابة", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "الطوارئ والإسعاف والرعاية الحادة" })).toBeInTheDocument();
    expect(screen.getByText("عرض اصطناعي معزول")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "الإسعاف والتوجيه" }));
    expect(screen.getByText("الإسعاف والتوجيه الاصطناعي")).toBeInTheDocument();
    expect(screen.getByText(/لا GPS أو Dispatch أو اتصال خارجي/)).toBeInTheDocument();
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listPatients).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();
  });

  it("لا يقرأ المرضى والأوامر قبل تفعيل workspace ثم يستخدم البوابة المحدودة", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "طبيب طوارئ", email: "doctor@example.invalid", role: "doctor" },
    } as ReturnType<typeof useAuth>);

    renderPage();
    expect(await screen.findByText("رعاية الرافدين الحادة")).toBeInTheDocument();
    expect(workspaceScopedReads.listPatients).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "تفعيل السياق" }));

    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalledWith("workspace-acute-1"));
    await waitFor(() => expect(workspaceScopedReads.listPatients).toHaveBeenCalledWith({ limit: 50 }));
    await waitFor(() => expect(workspaceScopedReads.listOrders).toHaveBeenCalledWith({ limit: 50 }));

    fireEvent.click(screen.getByRole("button", { name: "المرضى ضمن النطاق" }));
    expect(await screen.findByText("مريض رعاية حادة ضمن النطاق")).toBeInTheDocument();
    expect(screen.queryByText("patient-acute-1")).not.toBeInTheDocument();
  });

  it("يحجب الطوارئ والإسعاف وICU والعمليات والدم والمرضيات في Live", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "موظف طوارئ", email: "staff@example.invalid", role: "staff" },
    } as ReturnType<typeof useAuth>);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "تفعيل السياق" }));
    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "الطوارئ والفرز" }));
    expect(screen.getByText("عمليات الطوارئ والفرز محجوبة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "الإسعاف والتوجيه" }));
    expect(screen.getByText("Dispatch والإسعاف محجوبان")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "العناية الحرجة" }));
    expect(screen.getByText("العناية الحرجة وDevice Gateway محجوبان")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "العمليات" }));
    expect(screen.getByText("العمليات الجراحية محجوبة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "بنك الدم" }));
    expect(screen.getByText("بنك الدم محجوب")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "المرضيات والعينات" }));
    expect(screen.getByText("المرضيات وتتبع العينات محجوبان")).toBeInTheDocument();
  });
});
