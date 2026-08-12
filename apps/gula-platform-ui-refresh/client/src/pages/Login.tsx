import { Activity, ArrowLeft, Eye, FlaskConical, LockKeyhole, Mail, ShieldAlert } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

export default function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isCompactLayout, setIsCompactLayout] = useState(() =>
    typeof window !== "undefined" && window.matchMedia("(max-width: 900px)").matches,
  );

  useEffect(() => {
    const media = window.matchMedia("(max-width: 900px)");
    const syncLayout = () => setIsCompactLayout(media.matches);
    syncLayout();
    media.addEventListener("change", syncLayout);
    return () => media.removeEventListener("change", syncLayout);
  }, []);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("تسجيل الدخول غير متاح في هذه الواجهة حتى يتم ربط عقد المصادقة والجلسة الفعلي.");
  };

  return (
    <main className={`login-page${isCompactLayout ? " login-page--compact" : ""}`}>
      <section className={`login-layout${isCompactLayout ? " login-layout--compact" : ""}`} aria-label="تسجيل الدخول إلى منصة GULA">
        <div className="auth-brand" dir="rtl"><div className="auth-brand__grid" aria-hidden="true" /><div className="auth-brand__content"><div className="brand-lockup brand-lockup--light"><span className="brand-mark"><FlaskConical size={24} /></span><span className="brand-word"><b>GULA</b><small>إدارة المختبرات</small></span></div><div className="auth-copy"><span className="eyebrow"><Activity size={15} /> تجربة واجهة لإدارة المختبرات</span><h1>واجهة منظمة<br />تنتظر ربطًا موثوقًا.</h1><p>صُممت هذه الشاشة لتقديم تجربة دخول عربية واضحة، ولا تحاكي جلسة مستخدم أو تحقق هوية قبل ربط خدمة مصادقة معتمدة.</p></div><div className="medical-illustration" aria-hidden="true"><div className="illustration-orbit orbit-one" /><div className="illustration-orbit orbit-two" /><div className="flask-illustration"><div className="flask-neck" /><div className="flask-body"><span /><i /><em /></div></div><div className="molecule molecule-one" /><div className="molecule molecule-two" /><div className="molecule molecule-three" /></div><p className="auth-brand__footer"><ShieldAlert size={16} /> حالة الحماية تحددها خدمة الهوية عند الربط</p></div></div>
        <section className="auth-panel" dir="rtl"><div className="auth-form-wrap"><div className="mobile-brand"><span className="brand-mark"><FlaskConical size={21} /></span><b>GULA</b></div><header className="form-heading"><span className="form-kicker">الوصول الآمن</span><h2>تسجيل الدخول</h2><p>سيُفعَّل النموذج عند توصيل المصادقة وإدارة الجلسات.</p></header><form onSubmit={submit} noValidate><div className="form-field"><label htmlFor="email">البريد الإلكتروني</label><div className="field-control"><Mail size={19} /><input id="email" type="email" placeholder="name@example.com" dir="ltr" required aria-describedby={error ? "login-error" : undefined} /></div></div><div className="form-field"><div className="label-row"><label htmlFor="password">كلمة المرور</label><span className="muted-cell">استعادة الحساب غير متاحة</span></div><div className="field-control"><LockKeyhole size={19} /><input id="password" type={showPassword ? "text" : "password"} placeholder="••••••••" dir="ltr" required aria-describedby={error ? "login-error" : undefined} /><button type="button" className="password-toggle" aria-label={showPassword ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"} onClick={() => setShowPassword(!showPassword)}><Eye size={18} /></button></div></div><label className="check-row"><input type="checkbox" /><span>تذكر تفضيلات العرض على هذا الجهاز</span></label>{error ? <p id="login-error" className="form-error" role="alert">{error}</p> : null}<button className="primary-button login-button" type="submit">التحقق من حالة الربط <ArrowLeft size={18} /></button></form><p className="auth-help">تحتاج إلى مساعدة؟ <span className="muted-cell">يُحدد مسار الدعم عند ربط الخدمة.</span></p></div></section>
      </section>
    </main>
  );
}
