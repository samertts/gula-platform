import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Input, Button } from "@/components/ui";
import { authApi } from "@/api/endpoints";

function detailMessage(error: unknown) {
  const detail = (error as { response?: { data?: { detail?: string | { message_ar?: string; message?: string } } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return detail?.message_ar || detail?.message || "تعذر إكمال العملية";
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", phone: "", email: "", password: "", confirm_password: "" });
  const [verificationCode, setVerificationCode] = useState("");
  const [step, setStep] = useState<"register" | "verify">("register");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const identifier = form.email.trim().toLowerCase() || form.phone.trim();

  const update = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }));

  const handleRegister = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setMessage("");
    if (form.password !== form.confirm_password) {
      setError("كلمتا المرور غير متطابقتين");
      return;
    }
    setLoading(true);
    try {
      await authApi.registerCitizen({
        full_name: form.full_name,
        phone: form.phone,
        email: form.email || undefined,
        password: form.password,
      });
      const verification = await authApi.requestVerification(identifier);
      const demoCode = typeof verification.demo_code === "string" ? verification.demo_code : "";
      setMessage(demoCode ? `تم إنشاء الحساب. رمز العرض التجريبي: ${demoCode}` : "تم إنشاء الحساب. تحقق من بريدك أو هاتفك لإكمال التفعيل.");
      setStep("verify");
    } catch (err: unknown) {
      setError(detailMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.confirmVerification(identifier, verificationCode);
      navigate("/login");
    } catch (err: unknown) {
      setError(detailMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">إنشاء حساب مدني</CardTitle>
        <CardDescription>{step === "register" ? "أنشئ حسابًا ثم أكمل التحقق المجاني" : "أدخل رمز التحقق لإكمال تفعيل الحساب"}</CardDescription>
      </CardHeader>
      <CardContent>
        {error && <div className="mb-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">{error}</div>}
        {message && <div className="mb-4 rounded-md bg-primary/10 p-3 text-sm text-primary" role="status">{message}</div>}
        {step === "register" ? (
          <form onSubmit={handleRegister} className="space-y-4">
            <div className="space-y-2"><label className="text-sm font-medium" htmlFor="full_name">الاسم الكامل</label><Input id="full_name" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} required /></div>
            <div className="space-y-2"><label className="text-sm font-medium" htmlFor="phone">رقم الهاتف</label><Input id="phone" inputMode="tel" placeholder="+9647700000000" value={form.phone} onChange={(e) => update("phone", e.target.value)} required /></div>
            <div className="space-y-2"><label className="text-sm font-medium" htmlFor="register-email">البريد الإلكتروني (اختياري)</label><Input id="register-email" type="email" value={form.email} onChange={(e) => update("email", e.target.value)} /></div>
            <div className="space-y-2"><label className="text-sm font-medium" htmlFor="register-password">كلمة المرور</label><Input id="register-password" type="password" minLength={12} value={form.password} onChange={(e) => update("password", e.target.value)} required /><p className="text-xs text-muted-foreground">12 حرفًا على الأقل، مع حرف كبير وصغير ورقم ورمز.</p></div>
            <div className="space-y-2"><label className="text-sm font-medium" htmlFor="confirm-password">تأكيد كلمة المرور</label><Input id="confirm-password" type="password" value={form.confirm_password} onChange={(e) => update("confirm_password", e.target.value)} required /></div>
            <Button type="submit" className="w-full" loading={loading}>إنشاء الحساب</Button>
          </form>
        ) : (
          <form onSubmit={handleVerify} className="space-y-4">
            <div className="space-y-2"><label className="text-sm font-medium" htmlFor="verification-code">رمز التحقق المكون من 6 أرقام</label><Input id="verification-code" inputMode="numeric" maxLength={6} value={verificationCode} onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ""))} required /></div>
            <Button type="submit" className="w-full" loading={loading}>تأكيد الحساب</Button>
          </form>
        )}
        <p className="mt-5 text-center text-sm text-muted-foreground"><Link className="text-primary hover:underline" to="/login">العودة إلى تسجيل الدخول</Link></p>
      </CardContent>
    </Card>
  );
}
