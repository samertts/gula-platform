import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/api/client";
import { workspaceScopedReads } from "@/api/workspaceScopedReads";
import { useAuth } from "@/contexts/AuthContext";
import HospitalOperationsWorkspacePage from "./HospitalOperationsWorkspacePage";

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

const hospitalWorkspace = {
  id: "workspace-hospital-1",
  uuid: "workspace-hospital-1-uuid",
  workspace_type: "hospital",
  name: "Rafidain Hospital",
  name_ar: "مستشفى الرافدين",
  status: "ACTIVE",
  organization_id: "org-hospital-1",
  facility_id: "facility-hospital-1",
  department_id: "department-medicine-1",
  professional_type: "physician",
  is_personal: false,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/hospital-operations"]}>
        <HospitalOperationsWorkspacePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("HospitalOperationsWorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "مستشفى تجريبي", email: "hospital@example.invalid", role: "demo_viewer" },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [hospitalWorkspace] });
    vi.mocked(apiClient.switchWorkspace).mockResolvedValue({
      context: { account_id: "account-1", identity_id: "identity-1", workspace_id: hospitalWorkspace.id, version: 2 },
      workspace: hospitalWorkspace,
    });
    vi.mocked(workspaceScopedReads.listPatients).mockResolvedValue([
      { id: "patient-1", display_name: "مريض مستشفى ضمن النطاق", birth_date: null, gender: null, created_at: null },
    ]);
    vi.mocked(workspaceScopedReads.listOrders).mockResolvedValue([
      { id: "order-1", patient_display_name: "مريض مستشفى ضمن النطاق", practitioner_display_name: "طبيب ضمن الفريق", status: "active", test_count: 3, created_at: null },
    ]);
  });

  it("يعرض مسار المستشفى الاصطناعي دون API حي أو عمليات تشغيلية", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "عمليات المستشفى" })).toBeInTheDocument();
    expect(screen.getByText("عرض اصطناعي معزول")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "مركز الأسرة" }));
    expect(screen.getByText("مركز الأسرة الاصطناعي")).toBeInTheDocument();
    expect(screen.getByText("التخصيص والنقل وحالة العزل للعرض فقط؛ لا يظهر رقم مواطن أو موقع حقيقي.")).toBeInTheDocument();
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listPatients).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();
  });

  it("لا يقرأ المرضى والأوامر قبل تفعيل workspace ثم يستخدم البوابة المحدودة", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "موظف مستشفى", email: "hospital@example.invalid", role: "staff" },
    } as ReturnType<typeof useAuth>);

    renderPage();
    expect(await screen.findByText("مستشفى الرافدين")).toBeInTheDocument();
    expect(workspaceScopedReads.listPatients).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "تفعيل سياق المستشفى" }));

    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalledWith("workspace-hospital-1"));
    await waitFor(() => expect(workspaceScopedReads.listPatients).toHaveBeenCalledWith({ limit: 50 }));
    await waitFor(() => expect(workspaceScopedReads.listOrders).toHaveBeenCalledWith({ limit: 50 }));

    fireEvent.click(screen.getByRole("button", { name: "المرضى ضمن النطاق" }));
    expect(await screen.findByText("مريض مستشفى ضمن النطاق")).toBeInTheDocument();
    expect(screen.queryByText("patient-1")).not.toBeInTheDocument();
  });

  it("يحجب الطوارئ والإدخال والأسرة والعمليات والخروج في Live", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "موظف مستشفى", email: "hospital@example.invalid", role: "staff" },
    } as ReturnType<typeof useAuth>);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "تفعيل سياق المستشفى" }));
    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "الطوارئ والفرز" }));
    expect(screen.getByText("عمليات الطوارئ والفرز محجوبة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "الإدخال والإقامة" }));
    expect(screen.getByText("الإدخال والقبول محجوبان")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "مركز الأسرة" }));
    expect(screen.getByText("مركز الأسرة الحي محجوب")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "العمليات والعناية" }));
    expect(screen.getByText("العمليات والعناية المركزة محجوبة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "الخروج والمتابعة" }));
    expect(screen.getByText("الخروج والمتابعة محجوبان")).toBeInTheDocument();
  });
});
