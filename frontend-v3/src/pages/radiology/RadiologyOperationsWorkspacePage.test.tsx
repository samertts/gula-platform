import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/api/client";
import { radiologyApi } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import RadiologyOperationsWorkspacePage from "./RadiologyOperationsWorkspacePage";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

vi.mock("@/api/client", () => ({
  apiClient: {
    listWorkspaces: vi.fn(),
    switchWorkspace: vi.fn(),
  },
}));

vi.mock("@/api/endpoints", () => ({
  radiologyApi: {
    orders: vi.fn(),
    appointments: vi.fn(),
    exams: vi.fn(),
    radiologistWorklist: vi.fn(),
    technologistWorklist: vi.fn(),
  },
}));

const radiologyWorkspace = {
  id: "workspace-radiology-1",
  uuid: "workspace-radiology-1-uuid",
  workspace_type: "professional",
  name: "Radiology workspace",
  name_ar: "مساحة الأشعة المركزية",
  status: "ACTIVE",
  organization_id: "org-radiology-1",
  facility_id: "facility-radiology-1",
  department_id: "department-radiology-1",
  professional_type: "radiologist",
  is_personal: false,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/radiology-operations"]}>
        <RadiologyOperationsWorkspacePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("RadiologyOperationsWorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "اختصاصي أشعة تجريبي", email: "radiology@example.invalid", role: "demo_viewer" },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [radiologyWorkspace] });
    vi.mocked(apiClient.switchWorkspace).mockResolvedValue({
      context: { account_id: "account-1", identity_id: "identity-1", workspace_id: radiologyWorkspace.id, version: 2 },
      workspace: radiologyWorkspace,
    });
    vi.mocked(radiologyApi.orders).mockResolvedValue({
      total: 1,
      items: [{ id: "order-1", patient_id: "patient-1", modality: "CT", body_part: "Chest", priority: "urgent", status: "scheduled", clinical_indication: "Dyspnea", created_at: "2026-08-27T08:00:00Z" }],
    });
    vi.mocked(radiologyApi.appointments).mockResolvedValue({
      total: 1,
      items: [{ id: "appointment-1", order_id: "order-1", patient_id: "patient-1", modality: "CT", status: "scheduled", scheduled_date: "2026-08-27", scheduled_time: "09:30", room: "CT-1" }],
    });
    vi.mocked(radiologyApi.exams).mockResolvedValue({
      total: 1,
      items: [{ id: "exam-1", order_id: "order-1", patient_id: "patient-1", accession_number: "ACC-1", modality: "CT", body_part: "Chest", status: "completed", images_count: 120, series_count: 4, created_at: "2026-08-27T09:45:00Z" }],
    });
    vi.mocked(radiologyApi.radiologistWorklist).mockResolvedValue({
      total: 1,
      items: [{ id: "exam-1", accession_number: "ACC-1", modality: "CT", body_part: "Chest", status: "assigned", images_count: 120, series_count: 4 }],
    });
    vi.mocked(radiologyApi.technologistWorklist).mockResolvedValue({
      total: 1,
      items: [{ id: "exam-1", accession_number: "ACC-1", modality: "CT", body_part: "Chest", status: "in_progress", images_count: 120, series_count: 4 }],
    });
  });

  it("يعرض دورة الأشعة الاصطناعية دون استدعاء API حي أو صور حقيقية", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "الأشعة والتصوير الطبي" })).toBeInTheDocument();
    expect(screen.getByText("عرض اصطناعي معزول")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "الدراسات" }));
    expect(screen.getAllByText(/ACC-260827/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("عارض محجوب").length).toBeGreaterThan(0);
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
    expect(radiologyApi.orders).not.toHaveBeenCalled();
    expect(radiologyApi.exams).not.toHaveBeenCalled();
  });

  it("لا يقرأ الطلبات أو الدراسات قبل تفعيل سياق الأشعة ثم يستخدم العقود الخادمية", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "اختصاصي أشعة حي", email: "radiology@example.invalid", role: "doctor" },
    } as ReturnType<typeof useAuth>);

    renderPage();

    expect(await screen.findByText("مساحة الأشعة المركزية")).toBeInTheDocument();
    expect(radiologyApi.orders).not.toHaveBeenCalled();
    expect(radiologyApi.exams).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "تفعيل سياق الأشعة" }));

    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalledWith("workspace-radiology-1"));
    await waitFor(() => expect(radiologyApi.orders).toHaveBeenCalledWith({ limit: 50 }));
    await waitFor(() => expect(radiologyApi.appointments).toHaveBeenCalledWith({ limit: 50 }));
    await waitFor(() => expect(radiologyApi.exams).toHaveBeenCalledWith({ limit: 50 }));
    await waitFor(() => expect(radiologyApi.radiologistWorklist).toHaveBeenCalledWith());
    await waitFor(() => expect(radiologyApi.technologistWorklist).toHaveBeenCalledWith());

    fireEvent.click(screen.getByRole("button", { name: "طلبات التصوير" }));
    expect(await screen.findByText(/Chest/)).toBeInTheDocument();
    expect(screen.queryByText("patient-1")).not.toBeInTheDocument();
  });

  it("يحجب الصور والتقارير والتوقيع والاكتشافات الحرجة في Live", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "اختصاصي أشعة حي", email: "radiology@example.invalid", role: "doctor" },
    } as ReturnType<typeof useAuth>);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "تفعيل سياق الأشعة" }));
    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "التقارير" }));
    expect(screen.getByText("التقارير غير موصولة في هذه الموجة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "الاكتشافات الحرجة" }));
    expect(screen.getByText("الاكتشافات الحرجة غير موصولة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "عارض DICOM" }));
    expect(screen.getByText("عارض DICOM غير موصول")).toBeInTheDocument();
  });
});
