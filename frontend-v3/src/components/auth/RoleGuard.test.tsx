import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { RoleGuard } from "./RoleGuard";
import { useAuth } from "@/contexts/AuthContext";
import type { UserInfo } from "@/types";

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const mockedUseAuth = vi.mocked(useAuth);

function user(role: string): UserInfo {
  return {
    id: 1,
    name: "Test User",
    email: "test@example.invalid",
    role,
    lab_id: 3,
    lab_name: "Test Lab",
  };
}

/** Render a guarded route and report where the guard sent the user. */
function renderGuarded(roles: Parameters<typeof RoleGuard>[0]["roles"]) {
  return render(
    <MemoryRouter initialEntries={["/protected"]}>
      <Routes>
        <Route
          path="/protected"
          element={
            <RoleGuard roles={roles}>
              <p>protected content</p>
            </RoleGuard>
          }
        />
        <Route path="/dashboard" element={<p>dashboard fallback</p>} />
        <Route path="/login" element={<p>login page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

function auth(overrides: Partial<ReturnType<typeof useAuth>>) {
  mockedUseAuth.mockReturnValue({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    demoMode: false,
    memberships: [],
    effectivePermissions: {},
    refreshMemberships: vi.fn(),
    login: vi.fn(),
    startDemo: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  } as ReturnType<typeof useAuth>);
}

describe("RoleGuard", () => {
  it("sends an unauthenticated visitor to the login page", () => {
    auth({ user: null, isAuthenticated: false });
    renderGuarded(["admin"]);
    expect(screen.getByText("login page")).toBeTruthy();
    expect(screen.queryByText("protected content")).toBeNull();
  });

  it("lets an authorized role through", () => {
    auth({ user: user("admin"), isAuthenticated: true });
    renderGuarded(["master_admin", "admin"]);
    expect(screen.getByText("protected content")).toBeTruthy();
  });

  it("turns away an authenticated user whose role is not listed", () => {
    // The defect: this branch was guarded on demoMode, so outside a demo
    // session every signed-in user reached every guarded route.
    auth({ user: user("technician"), isAuthenticated: true, demoMode: false });
    renderGuarded(["master_admin", "admin"]);
    expect(screen.getByText("dashboard fallback")).toBeTruthy();
    expect(screen.queryByText("protected content")).toBeNull();
  });

  it("still turns away an unlisted demo persona", () => {
    // Demo behaviour is unchanged: the check already applied there.
    auth({ user: user("citizen"), isAuthenticated: true, demoMode: true });
    renderGuarded(["admin"]);
    expect(screen.getByText("dashboard fallback")).toBeTruthy();
  });

  it("still lets an authorized demo persona through", () => {
    auth({ user: user("doctor"), isAuthenticated: true, demoMode: true });
    renderGuarded(["doctor", "staff"]);
    expect(screen.getByText("protected content")).toBeTruthy();
  });

  it("honours an explicit fallback route", () => {
    auth({ user: user("citizen"), isAuthenticated: true });
    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <RoleGuard roles={["admin"]} fallback="/citizen">
                <p>protected content</p>
              </RoleGuard>
            }
          />
          <Route path="/citizen" element={<p>citizen workspace</p>} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("citizen workspace")).toBeTruthy();
  });

  it("decides on the role the server issued, and reads nothing else", () => {
    // The guard is navigation, not authorization. It must not consult
    // client-held permission state, and it must not grant anything: the
    // server stays the sole authority and still refuses the data behind any
    // route reached another way. Proven by giving the client every permission
    // and an active membership while the role stays unlisted.
    auth({
      user: user("technician"),
      isAuthenticated: true,
      effectivePermissions: { "org-1": ["system:admin", "billing:write"] },
      memberships: [
        { id: "m-1", organization_id: "org-1", status: "active" },
      ] as unknown as ReturnType<typeof useAuth>["memberships"],
    });
    renderGuarded(["admin"]);
    expect(screen.getByText("dashboard fallback")).toBeTruthy();
    expect(screen.queryByText("protected content")).toBeNull();
  });
});
