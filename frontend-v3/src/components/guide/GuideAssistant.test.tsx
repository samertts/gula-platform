import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "@/contexts/AuthContext";
import { useLocale } from "@/contexts/LocaleContext";
import { GuideAssistant } from "./GuideAssistant";

vi.mock("@/contexts/AuthContext", () => ({ useAuth: vi.fn() }));
vi.mock("@/contexts/LocaleContext", () => ({ useLocale: vi.fn() }));

describe("GuideAssistant", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({ demoMode: true } as ReturnType<typeof useAuth>);
    vi.mocked(useLocale).mockReturnValue({ locale: "ar", isRTL: true, setLocale: vi.fn() } as ReturnType<typeof useLocale>);
  });

  it("يعرض إرشادات Acute Care محلياً ويعلن أن المساعد بلا وصول مستقل", () => {
    render(<MemoryRouter initialEntries={["/acute-care-operations"]}><GuideAssistant /></MemoryRouter>);

    const assistant = screen.getByRole("complementary");
    expect(assistant).toHaveAttribute("data-assistant-state", "idle");
    fireEvent.click(screen.getByRole("button", { name: "المساعد" }));
    expect(assistant).toHaveAttribute("data-assistant-state", "responding");
    expect(screen.getByText(/الفرز يحدد الأولوية/)).toBeInTheDocument();
    expect(screen.getByText("مرشد محلي؛ لا يملك وصولًا مستقلاً إلى قاعدة البيانات")).toBeInTheDocument();
    expect(screen.getByText("وضع تجريبي: البيانات اصطناعية ومعزولة")).toBeInTheDocument();
  });
});
