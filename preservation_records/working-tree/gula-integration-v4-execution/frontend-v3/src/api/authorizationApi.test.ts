import { afterEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "./client";
import { authorizationApi } from "./endpoints";

describe("registered authorization bootstrap reads", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("calls the exact registered contract paths with GET only", async () => {
    const getSpy = vi.spyOn(apiClient.api, "get").mockImplementation(async (url: string) => {
      if (url === "/authz/me") {
        return { data: { user: { id: 7, role: "admin" } } };
      }
      if (url === "/authz/me/permissions") {
        return { data: { user_id: 7, permissions: ["lab:read"], count: 1 } };
      }
      if (url === "/authz/me/menu") {
        return { data: { menu: [{ id: "dashboard" }] } };
      }
      throw new Error(`unexpected path ${url}`);
    });

    const context = await authorizationApi.context();
    const permissions = await authorizationApi.permissions();
    const menu = await authorizationApi.menu();

    expect(context.user).toMatchObject({ id: 7 });
    expect(permissions.permissions).toEqual(["lab:read"]);
    expect(menu.menu).toEqual([{ id: "dashboard" }]);
    expect(getSpy.mock.calls.map((call) => call[0])).toEqual([
      "/authz/me",
      "/authz/me/permissions",
      "/authz/me/menu",
    ]);
  });

  it("does not convert malformed responses into permissions", async () => {
    vi.spyOn(apiClient.api, "get").mockResolvedValueOnce({
      data: { user_id: 7, permissions: "admin", count: 1 },
    } as never);

    const result = await authorizationApi.permissions();
    expect(Array.isArray(result.permissions)).toBe(false);
  });
});
