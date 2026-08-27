import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/api/client";
import { workspaceScopedReads } from "@/api/workspaceScopedReads";
import { useAuth } from "@/contexts/AuthContext";
import ClinicOperationsWorkspacePage from "./ClinicOperationsWorkspacePage";

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

const clinicWorkspace = {
  id: "workspace-clinic-1",
  uuid: "workspace-clinic-1-uuid",
  workspace_type: "professional",
  name: "Primary Care Clinic",
  name_ar: "عيادة الرعاية الأولية",
  status: "ACTIVE",
  organization_id: "org-clinic-1",
  facility_id: "facility-clinic-1",
  department_id: "department-clinic-1",
  professional_type: "physician",
  is_personal: false,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/clinic-operations"]}>
        <ClinicOperationsWorkspacePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ClinicOperationsWorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "طبيب تجريبي", email: "clinic@example.invalid", role: "demo_viewer" },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [clinicWorkspace] });
    vi.mocked(apiClient.switchWorkspace).mockResolvedValue({
      context: { account_id: "account-1", identity_id: "identity-1", workspace_id: clinicWorkspace.id, version: 2 },
      workspace: clinicWorkspace,
    });
    vi.mocked(workspaceScopedReads.listPatients).mockResolvedValue([
      { id: "patient-1", display_name: "مريض حي ضمن النطاق", birth_date: null, gender: null, created_at: null },
    ]);
    vi.mocked(workspaceScopedReads.listOrders).mockResolvedValue([
      { id: "order-1", patient_display_name: "مريض حي ضمن النطاق", practitioner_display_name: "طبيب ضمن السياق", status: "pending", test_count: 2, created_at: null },
    ]);
  });

  it("يعرض مسار العيادة الاصطناعي دون API حي أو كتابة سريرية", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "العيادة الطبية" })).toBeInTheDocument();
    expect(screen.getByText("عرض اصطناعي معزول")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "مساحة الزيارة" }));
    expect(screen.getByText(/Encounter تجريبي/)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /طلب مختبر|طلب أشعة|وصفة|إحالة|إغلاق الزيارة/ }).every((button) => (button as HTMLButtonElement).disabled)).toBe(true);
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listPatients).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();
  });

  it("لا يقرأ المرضى والطلبات قبل تفعيل workspace ثم يستخدم بوابة القراءة المحدودة", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "طبيب حي", email: "clinic@example.invalid", role: "doctor" },
    } as ReturnType<typeof useAuth>);

    renderPage();

    expect(await screen.findByText("عيادة الرعاية الأولية")).toBeInTheDocument();
    expect(workspaceScopedReads.listPatients).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "تفعيل سياق العيادة" }));

    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalledWith("workspace-clinic-1"));
    await waitFor(() => expect(workspaceScopedReads.listPatients).toHaveBeenCalledWith({ limit: 50 }));
    await waitFor(() => expect(workspaceScopedReads.listOrders).toHaveBeenCalledWith({ limit: 50 }));

    fireEvent.click(screen.getByRole("button", { name: "المرضى ضمن النطاق" }));
    expect(await screen.findByText("مريض حي ضمن النطاق")).toBeInTheDocument();
    expect(screen.queryByText("patient-1")).not.toBeInTheDocument();
  });

  it("يحجب المواعيد وEncounter والوصفة والإحالة في Live", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "طبيب حي", email: "clinic@example.invalid", role: "doctor" },
    } as ReturnType<typeof useAuth>);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "تفعيل سياق العيادة" }));
    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "المواعيد" }));
    expect(screen.getByText("المواعيد الحية غير موصولة بهذه الموجة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "مساحة الزيارة" }));
    expect(screen.getByText("Encounter والكتابة السريرية محجوبة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "خطة الرعاية" }));
    expect(screen.getByText("خطة الرعاية محجوبة")).toBeInTheDocument();
  });
});
