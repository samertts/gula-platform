import { HeartPulse, UserRound } from "lucide-react";

export default function Patients() {
  return <div className="page-stack page-enter"><section className="page-hero"><div><span className="section-kicker">السجل المركزي</span><h2>سجل المرضى</h2><p>ستُعرض المعلومات الأساسية وسجل الفحوصات بعد ربط عقد المرضى والسياق المصرح به.</p></div></section><section className="panel empty-directory" aria-live="polite"><div className="empty-directory__icon"><UserRound size={26} /></div><h3>سجل المرضى غير متاح للعرض بعد</h3><p>لا توجد بيانات مرضى معروضة لأن مصدر البيانات وعقد الإضافة والتفويض لم يُربطوا بهذه الواجهة. لن تُحاكي المنصة وجود ملفات أو عمليات سريرية قبل اكتمال الربط.</p><span className="helper-note"><HeartPulse size={16} /> ستُطبّق السرية والصلاحيات وسجل الوصول عند تفعيل العقد المعتمد.</span></section></div>;
}
