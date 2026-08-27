import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { OrganizationWorkspacePage } from "./OrganizationWorkspacePage";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

vi.mock("@/api/client", () => ({
  apiClient: {
    listWorkspaces: vi.fn(),
    listMyMemberships: vi.fn(),
  },
}));

const liveWorkspace = {
  id: "workspace-org-1",
  uuid: "workspace-org-1-uuid",
  workspace_type: "organization",
  name: "Organization workspace",
  name_ar: "مساحة المؤسسة الطبية",
  status: "ACTIVE",
  organization_id: "org-live-1",
  facility_id: "facility-live-1",
  department_id: "department-live-1",
  professional_type: null,
  is_personal: false,
};

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/organization-workspace"]}>
        <OrganizationWorkspacePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OrganizationWorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "مدير تجريبي", email: "org@example.invalid", role: "admin" },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue({ workspaces: [liveWorkspace] });
    vi.mocked(apiClient.listMyMemberships).mockResolvedValue({
      memberships: [
        {
          id: "membership-1",
          uuid: "membership-1-uuid",
          account_id: "account-secret-not-for-ui",
          identity_id: "identity-1",
          organization_id: "org-live-1",
          facility_id: "facility-live-1",
          department_id: "department-live-1",
          unit_id: null,
          workspace_id: "workspace-org-1",
          relationship_type: "employment",
          scope_type: "facility",
          status: "ACTIVE",
          source: "verified",
          expires_at: null,
          version: 3,
          is_active: true,
        },
      ],
    });
  });

  it("يعرض مؤسسة وفروعاً اصطناعية ولا يستدعي عقود Live في Demo", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "كيان صحي مستقل، وفروع متعددة، وصلاحيات محكومة" })).toBeInTheDocument();
    expect(screen.getByText("لا توجد مؤسسة حقيقية")).toBeInTheDocument();
    expect(screen.getByText("فرع بابل الطبي")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "العضويات والأدوار" }));
    expect(screen.getByText("المدير الطبي — تجريبي")).toBeInTheDocument();
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
    expect(apiClient.listMyMemberships).not.toHaveBeenCalled();
  });

  it("يقرأ المساحات والعضويات من الخادم ويعرض نطاق المؤسسة دون account_id", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "مدير حي", email: "org@example.invalid", role: "admin" },
    } as ReturnType<typeof useAuth>);

    renderPage();

    expect((await screen.findAllByText(/org-live-1/)).length).toBeGreaterThan(0);
    await waitFor(() => expect(apiClient.listWorkspaces).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(apiClient.listMyMemberships).toHaveBeenCalledTimes(1));
    expect(screen.getByText("مساحة المؤسسة الطبية")).toBeInTheDocument();
    expect(screen.queryByText("account-secret-not-for-ui")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "العضويات والأدوار" }));
    expect(await screen.findByText(/employment/)).toBeInTheDocument();
    expect(screen.queryByText("account-secret-not-for-ui")).not.toBeInTheDocument();
  });

  it("يعرض حجباً صريحاً عند فشل عقود المؤسسة بدلاً من استخدام Demo كبديل", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "مدير حي", email: "org@example.invalid", role: "admin" },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockRejectedValue(new Error("organization scope unavailable"));

    renderPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("تعذر عرض البيانات المؤسسية");
    expect(screen.queryByText("فرع بابل الطبي")).not.toBeInTheDocument();
  });
});
