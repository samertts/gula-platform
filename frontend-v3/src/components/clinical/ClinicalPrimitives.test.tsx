import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  ClinicalStatePanel,
  ClinicalStatusBadge,
  ClinicalTimeline,
  CriticalAlertBanner,
  PatientContextCard,
} from "./ClinicalPrimitives";

describe("ClinicalPrimitives", () => {
  it("يعلن حالات الوصول والحالات التشغيلية بطريقة قابلة للقراءة", () => {
    render(<ClinicalStatePanel state="forbidden" title="الوصول محجوب" description="السياق غير مصرح." />);

    expect(screen.getByRole("alert", { name: "الوصول محجوب" })).toBeInTheDocument();
    expect(screen.getByText("محجوب")).toBeInTheDocument();
    expect(screen.getByText("السياق غير مصرح.")).toBeInTheDocument();
  });

  it("يفرق الأولوية الحرجة بوسم ونص لا باللون وحده", () => {
    render(<ClinicalStatusBadge status="critical" />);

    expect(screen.getByText("حرج")).toBeInTheDocument();
  });

  it("يحجب سياق المريض عندما يكون النطاق غير مصرح", () => {
    render(<PatientContextCard name="مريض ضمن النطاق" restricted />);

    expect(screen.getByRole("alert", { name: "سياق المريض محجوب" })).toBeInTheDocument();
    expect(screen.getByText("أعاد الخادم نطاقاً لا يسمح بعرض تفاصيل هذا المريض في الشاشة الحالية.")).toBeInTheDocument();
  });

  it("يعرض التنبيه الحرج مع فصل الاستلام عن الإجراء", () => {
    render(<CriticalAlertBanner title="نتيجة حرجة" description="تحتاج مراجعة الفريق المسؤول." />);

    expect(screen.getByRole("alert", { name: "نتيجة حرجة" })).toBeInTheDocument();
    expect(screen.getByText("يحتاج استلاماً")).toBeInTheDocument();
    expect(screen.getByText("الاستلام لا يساوي الإجراء السريري.")).toBeInTheDocument();
  });

  it("يدعم التسلسل الفارغ والمحمّل دون إخفاء الحالة", () => {
    const { rerender } = render(<ClinicalTimeline events={[]} />);
    expect(screen.getByRole("status", { name: "لا توجد أحداث" })).toBeInTheDocument();

    rerender(<ClinicalTimeline events={[{ id: "event-1", date: "2026-08-27 09:00", label: "فحص اصطناعي", status: "loaded" }]} />);
    expect(screen.getByText("فحص اصطناعي")).toBeInTheDocument();
    expect(screen.getByText("محمّل")).toBeInTheDocument();
  });
});
