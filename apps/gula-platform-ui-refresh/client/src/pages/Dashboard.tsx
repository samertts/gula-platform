import { DatabaseZap, ShieldAlert } from "lucide-react";
import { UiState } from "@/components/UiStates";
import { trpc } from "@/lib/trpc";

export default function Dashboard() {
  const connection = trpc.integration.connectionStatus.useQuery();

  const statusLabel = connection.data?.label ?? "يتم فحص حالة الاتصال";
  const statusDescription = connection.data?.description ?? "تتحقق الواجهة من إعداد طبقة الربط دون الاتصال المباشر بالخلفية من المتصفح.";

  return (
    <div className="page-stack page-enter">
      <section className="page-hero">
        <div>
          <span className="section-kicker">لوحة المتابعة التشغيلية</span>
          <h2>نظرة عامة على المختبر</h2>
          <p>تعرض المؤشرات والطلبات عند ربط مصدر بيانات تشغيلي معتمد وصلاحية مستخدم مؤكدة.</p>
        </div>
        <span className="outline-button" aria-label={statusLabel}><DatabaseZap size={19} /> {statusLabel}</span>
      </section>
      <section className="panel" aria-label="حالة بيانات لوحة التحكم">
        {connection.isLoading ? (
          <UiState kind="loading" title="يتم فحص طبقة الربط" description="لا تُجرى طلبات تشغيلية أو تُعرض بيانات مختبرية أثناء الفحص." />
        ) : connection.isError ? (
          <UiState kind="error" title="تعذر قراءة حالة طبقة الربط" description="لم يُعرض أي محتوى تشغيلي. يمكن إعادة المحاولة بعد تحقق مسؤول النظام من الخدمة." onRetry={() => connection.refetch()} />
        ) : (
          <UiState
            kind="empty"
            title={statusLabel}
            description={`${statusDescription} العقد المرجعي: ${connection.data?.contractId ?? "غير متاح"}.`}
          />
        )}
      </section>
      <section className="insight-card" aria-label="ملاحظة تشغيلية">
        <div className="insight-icon"><ShieldAlert size={21} /></div>
        <div><h3>حالة الواجهة</h3><p>التصميم جاهز لعرض حالات التحميل والفراغ والخطأ، بينما يظل المحتوى التشغيلي معطّلًا إلى أن تُوصل العقود الفعلية.</p></div>
      </section>
    </div>
  );
}
