import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import GoldenPathReadinessPage from "./GoldenPathReadinessPage";

describe("GoldenPathReadinessPage", () => {
  it("يظهر جاهزية جزئية ولا يعلن GOLDEN PATH PASSED قبل العقود", () => {
    render(<MemoryRouter><GoldenPathReadinessPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "جاهزية الرحلة السريرية الذهبية" })).toBeInTheDocument();
    expect(screen.getByText("الأساس متاح جزئياً · 2/12 مراحل جاهزة")).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "مراحل الرحلة الذهبية" })).toBeInTheDocument();
    expect(screen.getByText("Appointment")).toBeInTheDocument();
    expect(screen.getByText("يحتاج عقد دورة الموعد ومنع التكرار")).toBeInTheDocument();
    expect(screen.queryByText("GOLDEN PATH PASSED")).not.toBeInTheDocument();
  });
});
