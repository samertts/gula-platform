import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import ScreenByScreenPage from "./ScreenByScreenPage";

describe("ScreenByScreenPage", () => {
  it("يعرض شاشة الترحيب ويعلن أن المعرض اصطناعي للقراءة فقط", () => {
    render(<MemoryRouter><ScreenByScreenPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "مخطط الواجهات الفعلية في شاشة واحدة" })).toBeInTheDocument();
    expect(screen.getByText("Demo فقط · قراءة فقط")).toBeInTheDocument();
    expect(screen.getByText("صحتك في مكان واحد")).toBeInTheDocument();
    expect(screen.getByText(/لا تتصل ببيانات حقيقية/)).toBeInTheDocument();
  });

  it("يتنقل بين دور المواطن وشاشة النتيجة دون أي كتابة محلية", () => {
    render(<MemoryRouter><ScreenByScreenPage /></MemoryRouter>);

    fireEvent.click(within(screen.getByRole("navigation", { name: "أدوار المعرض" })).getByRole("button", { name: /^المواطن/ }));
    expect(screen.getByRole("heading", { name: "الرئيسية الصحية" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /النتيجة المختبرية/ }));

    expect(screen.getByText("CBC · 25 Aug 2026")).toBeInTheDocument();
    expect(screen.getByText(/هذا تنبيه اصطناعي/)).toBeInTheDocument();
    expect(screen.getByText("Value + Unit")).toBeInTheDocument();
  });

  it("يعرض واجهة الإسعاف بأقل لمسّات ويبقي العمليات الحساسة محجوبة", () => {
    render(<MemoryRouter><ScreenByScreenPage /></MemoryRouter>);

    fireEvent.click(within(screen.getByRole("navigation", { name: "أدوار المعرض" })).getByRole("button", { name: /^الطوارئ/ }));
    fireEvent.click(screen.getByRole("button", { name: /تطبيق الإسعاف/ }));

    expect(screen.getByText(/ACTIVE INCIDENT/)).toBeInTheDocument();
    expect(screen.getByText(/لا GPS أو Dispatch أو ePCR/)).toBeInTheDocument();
    expect(screen.getByText("Handover")).toBeInTheDocument();
  });
});
