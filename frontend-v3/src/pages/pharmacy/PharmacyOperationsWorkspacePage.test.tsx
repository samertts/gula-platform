import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/api/client";
import { pharmacyApi } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import PharmacyOperationsWorkspacePage from "./PharmacyOperationsWorkspacePage";

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
  pharmacyApi: {
    summary: vi.fn(),
    stock: vi.fn(),
    drugs: vi.fn(),
  },
}));

const pharmacyWorkspace = {
  id: "workspace-pharmacy-1",
  uuid: "workspace-pharmacy-1-uuid",
  workspace_type: "professional",
  name: "Pharmacy workspace",
  name_ar: "مساحة الصيدلية المركزية",
  status: "ACTIVE",
  organization_id: "org-pharmacy-1",
  facility_id: "facility-pharmacy-1",
  department_id: "department-pharmacy-1",
  professional_type: "pharmacist",
  is_personal: false,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/pharmacy-operations"]}>
        <PharmacyOperationsWorkspacePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("PharmacyOperationsWorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "صيدلي تجريبي", email: "pharmacy@example.invalid", role: "demo_viewer" },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [pharmacyWorkspace] });
    vi.mocked(apiClient.switchWorkspace).mockResolvedValue({
      context: { account_id: "account-1", identity_id: "identity-1", workspace_id: pharmacyWorkspace.id, version: 2 },
      workspace: pharmacyWorkspace,
    });
    vi.mocked(pharmacyApi.summary).mockResolvedValue({
      period_days: 30,
      sale_count: 12,
      units_sold: 90,
      sales_total: "125000",
      cost_total: "85000",
      gross_profit: "40000",
      low_stock_count: 2,
      expiring_soon_count: 1,
      stagnant_items: [],
      synthetic: false,
    });
    vi.mocked(pharmacyApi.stock).mockResolvedValue([
      { id: "stock-1", drug_catalog_id: "drug-1", batch_id: "batch-1", quantity: 100, reserved_quantity: 10, available_quantity: 90, reorder_point: 20, storage_condition: "room" },
    ]);
    vi.mocked(pharmacyApi.drugs).mockResolvedValue({
      total: 1,
      items: [{ id: "drug-1", code: "PAR-500", name: "Paracetamol", name_ar: "باراسيتامول", generic_name: "Paracetamol", brand_name: null, barcode_gs1: null, is_active: true }],
    });
  });

  it("يعرض دورة الصيدلية الاصطناعية دون API حي أو أزرار صرف وبيع", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "إدارة الصيدلية والأدوية" })).toBeInTheDocument();
    expect(screen.getByText("عرض اصطناعي معزول")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "كتالوج الأدوية" }));
    expect(screen.getAllByText(/أموكسيسيلين/).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "إتمام البيع وإصدار الفاتورة" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "محاكاة الصرف" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "محاكاة استلام 100 وحدة" })).not.toBeInTheDocument();
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
    expect(pharmacyApi.summary).not.toHaveBeenCalled();
    expect(pharmacyApi.stock).not.toHaveBeenCalled();
  });

  it("لا يقرأ الكتالوج أو المخزون الحي قبل تفعيل سياق الصيدلية ثم يقرأ الملخص الخادمي", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "صيدلي حي", email: "pharmacy@example.invalid", role: "staff" },
    } as ReturnType<typeof useAuth>);

    renderPage();

    expect(await screen.findByText("مساحة الصيدلية المركزية")).toBeInTheDocument();
    expect(pharmacyApi.summary).not.toHaveBeenCalled();
    expect(pharmacyApi.stock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "تفعيل سياق الصيدلية" }));

    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalledWith("workspace-pharmacy-1"));
    await waitFor(() => expect(pharmacyApi.summary).toHaveBeenCalledWith(30));
    await waitFor(() => expect(pharmacyApi.stock).toHaveBeenCalledWith({ limit: 50 }));
    expect(screen.getAllByText(/125000 IQD/).length).toBeGreaterThan(0);
  });

  it("يحجب الصرف والمرتجعات والتحويلات والتنبيهات الحية حتى تتوفر عقودها", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "صيدلي حي", email: "pharmacy@example.invalid", role: "staff" },
    } as ReturnType<typeof useAuth>);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "تفعيل سياق الصيدلية" }));
    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "بيع سريع" }));
    expect(screen.getByText("عقد الصرف الحي يحتاج خطوة تحقق مخصصة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "الوصفات والصرف" }));
    expect(screen.getByText("عقد الوصفة والصرف غير مفعّل في هذه الواجهة")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "الحركات" }));
    expect(screen.getByText("عقد الحركات والتحويلات غير مفعّل")).toBeInTheDocument();
  });
});
