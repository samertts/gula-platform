import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import CitizenWorkspacePage from "./CitizenWorkspacePage";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn((url: string) => {
      const responses: Record<string, unknown> = {
        "/citizen-platform/me/dashboard": { upcoming_appointments: 2, lab_results_count: 3, medications_count: 1 },
        "/citizen-platform/me/profile": { id: "demo-citizen", name: "مواطن تجريبي", status: "active" },
        "/citizen-platform/me/health-summary": { id: "summary-1", name: "الملخص الصحي", status: "ready" },
        "/citizen-platform/me/appointments": [{ appointment_id: "appt-1", doctor_name: "طبيب تجريبي", status: "scheduled" }],
        "/citizen-platform/me/medications": [{ id: "med-1", name: "علاج تجريبي", status: "active" }],
        "/citizen-platform/me/medication-dispenses": { dispenses: [] },
        "/citizen-platform/me/lab-results": [{ result_id: "result-1", test_name: "تحليل اصطناعي", status: "released" }],
      };
      return Promise.resolve({ data: responses[url] ?? [] });
    }),
  },
}));

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <CitizenWorkspacePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CitizenWorkspacePage", () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "مواطن تجريبي", role: "citizen" },
    } as ReturnType<typeof useAuth>);
    vi.clearAllMocks();
  });

  it("renders the unified isolated demo experience and only performs approved reads", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: /كل ما يخص رحلتك الصحية/ })).toBeInTheDocument();
    expect(screen.getByText("بيانات اصطناعية فقط")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "مواعيدي" })).toBeInTheDocument();

    await waitFor(() => expect(vi.mocked(api.get)).toHaveBeenCalledTimes(7));
    expect(vi.mocked(api.get).mock.calls.every(([url]) => String(url).startsWith("/citizen-platform/me/"))).toBe(true);
  });

  it("switches to appointments without creating a write operation", async () => {
    renderPage();
    await screen.findByRole("heading", { name: /كل ما يخص رحلتك الصحية/ });

    fireEvent.click(screen.getByRole("tab", { name: "مواعيدي" }));

    expect(screen.getByRole("tabpanel", { name: "مواعيدي" })).toBeInTheDocument();
    expect(screen.getByText("طبيب تجريبي")).toBeInTheDocument();
    expect(vi.mocked(api.get).mock.calls.every(([url]) => String(url).startsWith("/citizen-platform/me/"))).toBe(true);
  });
});
