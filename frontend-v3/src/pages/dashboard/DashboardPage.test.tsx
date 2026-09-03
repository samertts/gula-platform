import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { dashboardApi } from "@/api/endpoints";
import { useAuth } from "@/contexts/AuthContext";
import { DashboardPage } from "./DashboardPage";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

vi.mock("@/api/endpoints", () => ({
  dashboardApi: {
    demo: vi.fn(() => ({ total_patients: 24, today_orders: 11, today_results: 17, critical_alerts: 2 })),
  },
}));

function renderDashboard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DashboardPage role-aware experience", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("presents a doctor-centered workspace with scoped clinical shortcuts", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "طبيب تجريبي", role: "doctor" },
    } as ReturnType<typeof useAuth>);

    renderDashboard();

    expect(await screen.findByRole("heading", { name: "مركز العمل السريري للطبيب" })).toBeInTheDocument();
    expect(screen.getByText("مساحة الطبيب")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /دليل المرضى/ })).toHaveAttribute("href", "/patient-management");
    expect(screen.getByRole("link", { name: /النتائج/ })).toHaveAttribute("href", "/results");
    expect(vi.mocked(dashboardApi.demo)).not.toHaveBeenCalled();
  });

  it("presents a clinic-centered workspace without enabling a write action", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "مدير تجريبي", role: "admin" },
    } as ReturnType<typeof useAuth>);

    renderDashboard();

    expect(await screen.findByRole("heading", { name: "مركز تشغيل العيادة" })).toBeInTheDocument();
    expect(screen.getByText("سياق المؤسسة")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /دليل المرضى/ })).toHaveAttribute("href", "/patient-management");
    expect(screen.getByRole("link", { name: /عمليات المختبر/ })).toHaveAttribute("href", "/lab-operations");
    expect(screen.queryByRole("button", { name: /إنشاء|حفظ|تأكيد/ })).not.toBeInTheDocument();
  });
});
