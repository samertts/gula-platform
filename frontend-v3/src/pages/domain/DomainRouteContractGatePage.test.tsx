import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import DomainRouteContractGatePage from "./DomainRouteContractGatePage";

describe("DomainRouteContractGatePage", () => {
  it("يعرض عقد المسار وحالة الصيانة الآمنة دون بيانات سريرية", () => {
    render(
      <MemoryRouter>
        <DomainRouteContractGatePage
          title="Appointments"
          description="مسار المواعيد"
          contract="CIT-004 / appointment lifecycle"
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Appointments" })).toBeInTheDocument();
    expect(screen.getByText("CIT-004 / appointment lifecycle")).toBeInTheDocument();
    expect(screen.getByRole("status", { name: "العقد غير مربوط بالواجهة بعد" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /مشاهدة شاشة المعاينة/ })).toHaveAttribute("href", "/screen-by-screen");
  });
});
