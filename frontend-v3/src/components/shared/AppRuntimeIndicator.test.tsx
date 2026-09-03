import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "@/contexts/AuthContext";
import { AppRuntimeIndicator } from "./AppRuntimeIndicator";

vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));

describe("AppRuntimeIndicator", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window.navigator, "onLine", { configurable: true, value: true });
  });

  it("يعلن Demo بلا API أو بيانات حقيقية", () => {
    vi.mocked(useAuth).mockReturnValue({ demoMode: true } as ReturnType<typeof useAuth>);
    render(<AppRuntimeIndicator />);
    expect(screen.getByRole("status", { name: "وضع المعاينة: لا اتصال ببيانات حقيقية" })).toBeInTheDocument();
  });

  it("يعكس offline/online من المتصفح دون إنشاء طابور مزامنة", () => {
    vi.mocked(useAuth).mockReturnValue({ demoMode: false } as ReturnType<typeof useAuth>);
    render(<AppRuntimeIndicator />);
    expect(screen.getByRole("status", { name: "متصل بالشبكة" })).toBeInTheDocument();
    fireEvent(window, new Event("offline"));
    expect(screen.getByRole("status", { name: "دون اتصال بالشبكة" })).toBeInTheDocument();
  });
});
