import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { apiClient } from "@/api/client";
import { AuthProvider, useAuth } from "./AuthContext";

function Wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

function response(data: unknown) {
  return { data } as never;
}

describe("AuthContext authorization bootstrap", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("reads the three registered authorization contracts in a live session", async () => {
    const getSpy = vi.spyOn(apiClient.api, "get").mockImplementation(async (url: string) => {
      if (url === "/session") {
        return response({ user: { id: 7, role: "admin", lab_id: 1 }, demo_mode: false });
      }
      if (url === "/niam/memberships/me") {
        return response({ memberships: [] });
      }
      if (url === "/authz/me") {
        return response({ user: { id: 7, role: "admin" } });
      }
      if (url === "/authz/me/permissions") {
        return response({ user_id: 7, permissions: ["lab:read", "lab:manage"], count: 2 });
      }
      if (url === "/authz/me/menu") {
        return response({ menu: [{ id: "dashboard" }] });
      }
      throw new Error(`unexpected GET ${url}`);
    });

    const { result } = renderHook(() => useAuth(), { wrapper: Wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await waitFor(() =>
      expect(result.current.authorizationPermissions).toEqual(["lab:read", "lab:manage"]),
    );
    expect(result.current.authorizationContext).toMatchObject({ user: { id: 7 } });
    expect(result.current.authorizationMenu).toEqual([{ id: "dashboard" }]);
    for (const path of ["/authz/me", "/authz/me/permissions", "/authz/me/menu"]) {
      expect(getSpy).toHaveBeenCalledWith(path);
    }
  });

  it("fails closed when an authorization bootstrap read fails", async () => {
    vi.spyOn(apiClient.api, "get").mockImplementation(async (url: string) => {
      if (url === "/session") {
        return response({ user: { id: 8, role: "viewer", lab_id: 1 }, demo_mode: false });
      }
      if (url === "/niam/memberships/me") {
        return response({ memberships: [] });
      }
      if (url.startsWith("/authz/")) {
        throw new Error("authorization service unavailable");
      }
      throw new Error(`unexpected GET ${url}`);
    });

    const { result } = renderHook(() => useAuth(), { wrapper: Wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await waitFor(() => expect(result.current.authorizationContext).toBeNull());
    expect(result.current.authorizationPermissions).toEqual([]);
    expect(result.current.authorizationMenu).toEqual([]);
  });

  it("makes no authorization network call in demo mode", async () => {
    window.sessionStorage.setItem("gula_demo_active", "true");
    const getSpy = vi.spyOn(apiClient.api, "get");

    const { result } = renderHook(() => useAuth(), { wrapper: Wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.demoMode).toBe(true);
    expect(result.current.authorizationPermissions).toEqual([]);
    expect(getSpy.mock.calls.map((call) => call[0])).not.toContain("/authz/me");
  });
});
