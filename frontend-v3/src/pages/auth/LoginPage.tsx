import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, Input, Button } from "@/components/ui";
import { FlaskConical, ShieldCheck } from "lucide-react";

function errorMessage(error: unknown) {
  const detail = (error as { response?: { data?: { detail?: string | { message?: string; message_ar?: string } } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail?.message_ar) return detail.message_ar;
  return "فشل تسجيل الدخول";
}

export function LoginPage() {
  const { login, startDemo } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email, password });
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setError("");
    setDemoLoading(true);
    try {
      await startDemo();
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(errorMessage(err) || "الوضع التجريبي غير متاح حاليًا");
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="text-center">
        <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <FlaskConical className="h-6 w-6 text-primary" />
        </div>
        <CardTitle className="text-2xl">تسجيل الدخول</CardTitle>
        <CardDescription>أدخل بيانات الاعتماد الخاصة بك للوصول إلى النظام</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">
              {error}
            </div>
          )}
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="email">البريد الإلكتروني أو رقم الهاتف</label>
            <Input id="email" type="text" placeholder="name@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="password">كلمة المرور</label>
            <Input id="password" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <Button type="submit" className="w-full" loading={loading}>تسجيل الدخول</Button>
        </form>

        <div className="my-5 flex items-center gap-3 text-xs text-muted-foreground">
          <span className="h-px flex-1 bg-border" />
          <span>أو</span>
          <span className="h-px flex-1 bg-border" />
        </div>

        <button
          type="button"
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-2.5 text-sm font-medium text-amber-800 transition hover:bg-amber-500/20 dark:text-amber-200 disabled:cursor-not-allowed disabled:opacity-60"
          onClick={handleDemo}
          disabled={demoLoading || loading}
        >
          <ShieldCheck className="h-4 w-4" />
          {demoLoading ? "جاري فتح العرض التجريبي..." : "مشاهدة المنصة بالوضع التجريبي"}
        </button>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          البيانات في الوضع التجريبي اصطناعية ومعزولة ولا تمنح أي وصول إلى المنصة الحقيقية.
        </p>
        <p className="mt-4 text-center text-sm text-muted-foreground">
          <a className="text-primary hover:underline" href="/register">إنشاء حساب جديد</a>
        </p>
      </CardContent>
    </Card>
  );
}
