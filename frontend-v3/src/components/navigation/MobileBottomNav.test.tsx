import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MobileBottomNav } from "./MobileBottomNav";

const authState = {
  user: { role: "doctor" },
  demoMode: true,
  effectivePermissions: {} as Record<string, string[]>,
};

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => authState,
}));

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) =>
      ({
        "nav.dashboard": "Dashboard",
        "nav.patients": "Patients",
        "nav.orders": "Orders",
        "nav.results": "Results",
        "nav.alerts": "Alerts",
        "mobileNav.quickNavigation": "Quick navigation",
        "mobileNav.openAllSections": "Open all sections",
        "mobileNav.moreSections": "More sections",
        "mobileNav.more": "More",
        "mobileNav.current": "Current page",
      })[key] ?? key,
  }),
}));

describe("MobileBottomNav", () => {
  beforeEach(() => {
    authState.demoMode = true;
    authState.effectivePermissions = {};
  });

  it("uses translated labels and marks a nested route as current", () => {
    render(
      <MemoryRouter initialEntries={["/orders/123"]}>
        <MobileBottomNav onOpenMenu={vi.fn()} />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("navigation", { name: "Quick navigation" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Orders — Current page" }),
    ).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Patients" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "More sections" }),
    ).toHaveAttribute("aria-expanded", "false");
  });

  it("keeps live-mode navigation hidden until server-reflected permissions exist", () => {
    authState.demoMode = false;
    authState.effectivePermissions = {};

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <MobileBottomNav onOpenMenu={vi.fn()} />
      </MemoryRouter>,
    );

    expect(
      screen.queryByRole("link", { name: "Patients" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Orders" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Results" }),
    ).not.toBeInTheDocument();
  });

  it("announces an open menu state", () => {
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <MobileBottomNav onOpenMenu={vi.fn()} isMenuOpen />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("button", { name: "More sections" }),
    ).toHaveAttribute("aria-expanded", "true");
  });
});
