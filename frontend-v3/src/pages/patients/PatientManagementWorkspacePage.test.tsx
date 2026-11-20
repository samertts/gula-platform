import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "@/contexts/AuthContext";
import { PatientManagementWorkspacePage } from "./PatientManagementWorkspacePage";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

describe("PatientManagementWorkspacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fails closed for a live session instead of rendering synthetic patient data", () => {
    vi.mocked(useAuth).mockReturnValue({ demoMode: false } as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <PatientManagementWorkspacePage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "إدارة المرضى" })).toBeInTheDocument();
    expect(screen.getByText("القراءة المؤسسية معلّقة بأمان")).toBeInTheDocument();
    expect(screen.queryByText("سارة عبد الرحمن")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /العودة إلى لوحة العمل الآمنة/ })).toHaveAttribute("href", "/dashboard");
  });

  it("keeps the Medicare-inspired patient journey available in isolated demo mode", () => {
    vi.mocked(useAuth).mockReturnValue({ demoMode: true } as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <PatientManagementWorkspacePage />
      </MemoryRouter>,
    );

    expect(screen.getByText("وضع تجريبي معزول")).toBeInTheDocument();
    expect(screen.getAllByText("سارة عبد الرحمن").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "المواعيد" })).toBeInTheDocument();
  });
});
