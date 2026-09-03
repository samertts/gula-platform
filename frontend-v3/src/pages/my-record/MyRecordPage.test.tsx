import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import { apiClient } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import MyRecordPage from "./MyRecordPage";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

vi.mock("@/api/client", () => ({
  apiClient: {
    listWorkspaces: vi.fn(),
    listMyConsents: vi.fn(),
    withdrawConsent: vi.fn(),
    switchWorkspace: vi.fn(),
  },
}));

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/my-record"]}>
        <MyRecordPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const liveConsents = {
  consents: [
    {
      id: "consent-1",
      uuid: "consent-uuid-1",
      subject_account_id: "account-1",
      grantee_account_id: "account-2",
      purpose: "متابعة علاجية",
      scope: { laboratory_results: true },
      resource_domain: "نتائج المختبر",
      status: "ACTIVE",
      granted_at: "2026-08-27T08:00:00Z",
      withdrawn_at: null,
      expires_at: "2026-08-28T08:00:00Z",
      version: 1,
      source: "citizen",
      legal_basis: null,
      supersedes_id: null,
      reason: null,
    },
  ],
};

const liveWorkspaces = {
  workspaces: [
    {
      id: "workspace-citizen",
      uuid: "citizen-uuid",
      workspace_type: "citizen",
      name: "Citizen Workspace",
      name_ar: "مساحة المواطن",
      status: "active",
      organization_id: null,
      facility_id: null,
      department_id: null,
      professional_type: null,
      is_personal: true,
    },
    {
      id: "workspace-physician",
      uuid: "physician-uuid",
      workspace_type: "professional",
      name: "Physician Workspace",
      name_ar: "المساحة المهنية",
      status: "active",
      organization_id: "org-1",
      facility_id: "facility-1",
      department_id: "department-1",
      professional_type: "physician",
      is_personal: false,
    },
  ],
};

describe("MyRecordPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({
      demoMode: false,
      user: { name: "سالم تجريبي", email: "samer@example.invalid", role: "doctor", is_verified: true },
    } as ReturnType<typeof useAuth>);
    vi.mocked(apiClient.listWorkspaces).mockResolvedValue(liveWorkspaces);
    vi.mocked(apiClient.listMyConsents).mockResolvedValue(liveConsents);
    vi.mocked(apiClient.withdrawConsent).mockResolvedValue(liveConsents.consents[0]);
    vi.mocked(apiClient.switchWorkspace).mockResolvedValue({
      context: { account_id: "account-1", identity_id: "identity-1", workspace_id: "workspace-physician", version: 2 },
      workspace: liveWorkspaces.workspaces[1],
    });
  });

  it("renders only server-reflected workspaces and never exposes raw national identity data", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: "هوية واحدة، وسياقات صحية واضحة" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "مساحة المواطن" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "مساحة طبيب" })).toBeInTheDocument();
    expect(screen.getByText("لا يظهر رقم وطني أو معرف صحي خام")).toBeInTheDocument();
    expect(screen.queryByText("national_id")).not.toBeInTheDocument();
    expect(screen.queryByText("health_id")).not.toBeInTheDocument();
    expect(apiClient.listWorkspaces).toHaveBeenCalledTimes(1);
  });

  it("renders only server-reflected active consent metadata", async () => {
    renderPage();

    expect(await screen.findByText("نتائج المختبر")).toBeInTheDocument();
    expect(screen.getByText("حتى ٢٨‏/٨‏/٢٠٢٦ · نطاق محدد")).toBeInTheDocument();
    expect(apiClient.listMyConsents).toHaveBeenCalledWith();
  });

  it("withdraws access only through the server consent endpoint", async () => {
    renderPage();

    const withdrawButton = await screen.findByRole("button", { name: "إلغاء الوصول" });
    fireEvent.click(withdrawButton);

    await waitFor(() => expect(apiClient.withdrawConsent).toHaveBeenCalledWith("consent-1"));
    expect(apiClient.withdrawConsent).toHaveBeenCalledTimes(1);
  });

  it("switches context only through the server workspace endpoint", async () => {
    renderPage();
    await screen.findByText("مساحة طبيب");

    const switchButtons = screen.getAllByRole("button", { name: "تبديل السياق" });
    fireEvent.click(switchButtons[1]!);

    await waitFor(() => expect(apiClient.switchWorkspace).toHaveBeenCalledWith("workspace-physician"));
    expect(apiClient.switchWorkspace).toHaveBeenCalledTimes(1);
  });

  it("has no automated accessibility violations in the live shell", async () => {
    const { container } = renderPage();
    await screen.findByRole("heading", { name: "هوية واحدة، وسياقات صحية واضحة" });

    const results = await axe(container, { rules: { "color-contrast": { enabled: false } } });
    expect(results.violations).toEqual([]);
  });


  it("keeps demo synthetic and does not request live workspaces", async () => {
    vi.mocked(useAuth).mockReturnValue({
      demoMode: true,
      user: { name: "مواطن تجريبي", email: "demo@example.invalid", role: "citizen", is_verified: true },
    } as ReturnType<typeof useAuth>);

    renderPage();

    expect(await screen.findByText("مساحة المواطن التجريبية")).toBeInTheDocument();
    expect(screen.getByText("اصطناعية")).toBeInTheDocument();
    expect(apiClient.listWorkspaces).not.toHaveBeenCalled();
    expect(apiClient.listMyConsents).not.toHaveBeenCalled();
    expect(apiClient.withdrawConsent).not.toHaveBeenCalled();
    expect(apiClient.switchWorkspace).not.toHaveBeenCalled();
  });
});
