import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/api/client";
import { workspaceScopedReads } from "@/api/workspaceScopedReads";
import { useAuth } from "@/contexts/AuthContext";
import { LabOperationsWorkspacePage } from "./LabOperationsWorkspacePage";

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
    listOrders: vi.fn(),
  },
}));

const labWorkspace = {
  id: "workspace-lab-1",
  uuid: "workspace-lab-1-uuid",
  workspace_type: "professional",
  name: "Lab Workspace",
  name_ar: "مساحة المختبر المركزي",
  status: "ACTIVE",
  organization_id: "org-lab-1",
  facility_id: "facility-lab-1",
  department_id: "department-lab-1",
  professional_type: "laboratory",
  is_personal: false,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/lab-operations"]}>
        <LabOperationsWorkspacePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("LabOperationsWorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "مسؤول مختبر تجريبي", email: "lab@example.invalid", role: "lab_admin" },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [labWorkspace] });
    vi.mocked(apiClient.switchWorkspace).mockResolvedValue({
      context: { account_id: "account-1", identity_id: "identity-1", workspace_id: labWorkspace.id, version: 2 },
      workspace: labWorkspace,
    });
    vi.mocked(workspaceScopedReads.listOrders).mockResolvedValue([
      { id: "order-1", patient_display_name: "مريض ضمن النطاق", status: "pending", test_count: 2, created_at: "2026-08-27T08:00:00Z" },
    ]);
  });

  it("يعرض دورة المختبر الاصطناعية دون استدعاء Live أو أزرار تحقق وكتابة", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "إدارة المختبر" })).toBeInTheDocument();
    expect(screen.getByText("عرض اصطناعي معزول")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "العينات" }));
    expect(screen.getAllByText(/ACC-260814-0018/).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /محاكاة|بدء الفحص|تحديث|إصدار/ })).not.toBeInTheDocument();
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();
  });

  it("لا يقرأ الطلبات الحية قبل سياق المختبر، ثم يستخدم clinical gateway بعد تبديله", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "مسؤول مختبر حي", email: "lab@example.invalid", role: "lab_admin" },
    } as ReturnType<typeof useAuth>);

    renderPage();

    expect(await screen.findByText("مساحة المختبر المركزي")).toBeInTheDocument();
    expect(workspaceScopedReads.listOrders).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "تفعيل سياق المختبر" }));

    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalledWith("workspace-lab-1"));
    await waitFor(() => expect(workspaceScopedReads.listOrders).toHaveBeenCalledWith({ limit: 50 }));
    expect(screen.getByText("طلب ضمن النطاق")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "العينات" }));
    expect(screen.getByText("عقد قراءة العينات غير مفعّل")).toBeInTheDocument();
  });

  it("يحجب النتائج والأجهزة والجودة في Live بدلاً من اختلاق عقود LIS", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "مسؤول مختبر حي", email: "lab@example.invalid", role: "lab_admin" },
    } as ReturnType<typeof useAuth>);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "تفعيل سياق المختبر" }));
    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "النتائج" }));
    expect(screen.getByText("عقد قراءة النتائج غير مفعّل")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "المحللات" }));
    expect(screen.getByText("عقد المحللات والتكامل غير مفعّل")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "ضبط الجودة" }));
    expect(screen.getByText("عقد الجودة غير مفعّل")).toBeInTheDocument();
  });
});
