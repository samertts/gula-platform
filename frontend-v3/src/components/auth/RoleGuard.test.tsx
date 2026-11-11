import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "@/contexts/AuthContext";
import { RoleGuard } from "./RoleGuard";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

function renderGuard(role: string, demoMode: boolean) {
  vi.mocked(useAuth).mockReturnValue({
    isLoading: false,
    user: { role },
    demoMode,
  } as ReturnType<typeof useAuth>);

  return render(
    <MemoryRouter initialEntries={["/protected"]}>
      <Routes>
        <Route
          path="/protected"
          element={
            <RoleGuard roles={["admin"]}>
              <div>protected content</div>
            </RoleGuard>
          }
        />
        <Route path="/dashboard" element={<div>dashboard fallback</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RoleGuard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("enforces role restrictions in live mode", async () => {
    renderGuard("doctor", false);

    expect(screen.queryByText("protected content")).not.toBeInTheDocument();
    expect(await screen.findByText("dashboard fallback")).toBeInTheDocument();
  });

  it("allows the permitted role in live mode", () => {
    renderGuard("admin", false);

    expect(screen.getByText("protected content")).toBeInTheDocument();
    expect(screen.queryByText("dashboard fallback")).not.toBeInTheDocument();
  });

  it("keeps demo role restrictions enforced", async () => {
    renderGuard("doctor", true);

    expect(screen.queryByText("protected content")).not.toBeInTheDocument();
    expect(await screen.findByText("dashboard fallback")).toBeInTheDocument();
  });
});
