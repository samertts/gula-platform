import { HeartPulse, UserRound } from "lucide-react";
import { UiState } from "@/components/UiStates";
import { trpc } from "@/lib/trpc";

export default function Patients() {
  const patients = trpc.patients.list.useQuery({ limit: 25 });
  const result = patients.data;
  const isReady = result?.state === "ready";

  return <div className="page-stack page-enter" data-contract-id="patients.read" data-permission="patients:read" data-workspace-context="required"><section className="page-hero"><div><span className="section-kicker">السجل المركزي</span><h2>سجل المرضى</h2><p>يعرض هذا السطح الحد الأدنى من البيانات بعد التحقق الخادمي من سياق المختبر وصلاحية القراءة.</p></div></section>
    {patients.isLoading ? <UiState kind="loading" title="يجري التحقق من سياق المنشأة" description="لن يُطلب سجل المرضى قبل تحقق الخادم من الربط والصلاحية." /> : patients.isError ? <UiState kind="error" title="يتطلب السجل جلسة مستخدم" description="سجّل الدخول أولًا ثم أعد المحاولة. لا تُعرض أي بيانات عند تعذر إثبات الجلسة." onRetry={() => patients.refetch()} /> : !isReady ? <section className="panel empty-directory" aria-live="polite"><div className="empty-directory__icon"><UserRound size={26} /></div><h3>{result?.label ?? "سجل المرضى غير متاح"}</h3><p>{result?.description ?? "لا توجد بيانات مرضى معروضة قبل اكتمال التحقق الخادمي."}</p><span className="helper-note"><HeartPulse size={16} /> العقد المرجعي: {result?.contractId ?? "patients.read"} — الصلاحية المطلوبة: {result?.requiredPermission ?? "patients:read"}</span></section> : result.items?.length === 0 ? <UiState kind="empty" title="لا توجد سجلات مطابقة" description="تم التحقق من السياق والصلاحية، لكن العقد لم يُعد سجلات ضمن نطاق العرض الحالي." /> : <section className="panel order-table-panel" aria-live="polite"><div className="orders-summary"><span><UserRound size={16} /> {result.total ?? result.items?.length ?? 0} سجلًا ضمن النطاق الموثق</span><span>البيانات المعروضة مقتصرة على حقول العرض الدنيا</span></div><div className="table-wrap"><table><thead><tr><th>الاسم</th><th>المعرف الصحي</th><th>تاريخ الإنشاء</th></tr></thead><tbody>{result.items?.map((patient) => <tr key={patient.id}><td>{patient.fullName}</td><td>{patient.healthId ?? "—"}</td><td>{patient.createdAt ? new Date(patient.createdAt).toLocaleDateString("ar-IQ") : "—"}</td></tr>)}</tbody></table></div></section>}</div>;
}
