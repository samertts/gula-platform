import { FileBarChart2, ShieldCheck } from "lucide-react";

export default function Reports() {
  return <div className="page-stack page-enter"><section className="page-hero"><div><span className="section-kicker">تحليلات الأداء</span><h2>التقارير</h2><p>ستُعرض مؤشرات الإنتاجية والملفات القابلة للتنزيل بعد ربط خدمة التقارير مع سياق المختبر وصلاحيات المستخدم.</p></div></section><section className="panel empty-directory" aria-live="polite"><div className="empty-directory__icon"><FileBarChart2 size={26} /></div><h3>لا توجد تقارير تشغيلية معروضة</h3><p>أُزيلت المؤشرات والملفات التمثيلية من هذه الصفحة. لا تظهر النتائج أو التنزيلات إلا عند وجود عقد تقارير فعلي، وبيانات نطاق عمل، وصلاحية تحقق مناسبة.</p><span className="helper-note"><ShieldCheck size={16} /> سيُوثق مصدر كل تقرير وفترة بياناته وصلاحية الوصول إليه عند الربط.</span></section></div>;
}
