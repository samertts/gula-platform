import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, Input, Button, Badge } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { useAuth } from "@/contexts/AuthContext";
import { mfaApi, authApi } from "@/api/endpoints";
import { User, Mail, Shield, Building2, KeyRound, Smartphone } from "lucide-react";
import { formatDateTime, getErrorMessage } from "@/lib/utils";

export function ProfilePage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [toast, setToast] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const { data: mfaStatus } = useQuery({
    queryKey: ["mfa-status"],
    queryFn: () => mfaApi.status(),
  });

  const showToast = (kind: "success" | "error", message: string) => {
    setToast({ kind, message });
    window.setTimeout(() => setToast(null), 4000);
  };

  const changePasswordMutation = useMutation({
    mutationFn: () => authApi.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordError("");
      showToast("success", t("profile.passwordChanged"));
    },
    onError: (err) => {
      setPasswordError(getErrorMessage(err));
      showToast("error", getErrorMessage(err));
    },
  });

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError("");
    if (newPassword.length < 8) {
      setPasswordError(t("validation.minLength", { min: 8 }));
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError(t("validation.passwordMatch"));
      return;
    }
    changePasswordMutation.mutate();
  };

  return (
    <div className="space-y-6">
      <PageHeader title={t("profile.title")} description={t("profile.subtitle")} />

      {toast && (
        <div
          className={
            toast.kind === "success"
              ? "rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700 dark:bg-green-950 dark:text-green-300"
              : "rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300"
          }
          role="status"
        >
          {toast.message}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardContent className="flex flex-col items-center p-6 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 text-3xl font-bold text-primary">
              {user?.name?.charAt(0) || "U"}
            </div>
            <h2 className="mt-4 text-xl font-bold">{user?.name}</h2>
            <p className="text-sm text-muted-foreground">{user?.email}</p>
            <Badge className="mt-2">{user?.role}</Badge>
            <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
              <Smartphone className="h-4 w-4" />
              {t("profile.mfaStatus")}:
              <Badge variant={mfaStatus?.mfa_enabled ? "default" : "outline"}>
                {mfaStatus?.mfa_enabled ? t("profile.mfaEnabled") : t("profile.mfaDisabled")}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader><CardTitle>{t("profile.accountInfo")}</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2"><User className="h-4 w-4" /> {t("profile.name")}</label>
                <Input value={user?.name || ""} readOnly />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2"><Mail className="h-4 w-4" /> {t("profile.email")}</label>
                <Input value={user?.email || ""} readOnly />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2"><Shield className="h-4 w-4" /> {t("profile.role")}</label>
                <Input value={user?.role || ""} readOnly />
              </div>
              {user?.lab_name && (
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2"><Building2 className="h-4 w-4" /> {t("profile.lab")}</label>
                  <Input value={user.lab_name} readOnly />
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <KeyRound className="h-5 w-5" /> {t("profile.changePassword")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handlePasswordSubmit} className="space-y-4">
                {passwordError && (
                  <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{passwordError}</div>
                )}
                <div className="space-y-2">
                  <label className="text-sm font-medium">{t("profile.currentPassword")}</label>
                  <Input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">{t("profile.newPassword")}</label>
                    <Input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">{t("profile.confirmPassword")}</label>
                    <Input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <Button type="submit" loading={changePasswordMutation.isPending}>
                  {t("profile.updatePassword")}
                </Button>
              </form>
            </CardContent>
          </Card>

          {mfaStatus && mfaStatus.devices.length > 0 && (
            <Card>
              <CardHeader><CardTitle>{t("profile.mfaDevices")}</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {mfaStatus.devices.map((device) => (
                  <div key={device.id} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Smartphone className="h-4 w-4 text-muted-foreground" />
                      <span>{device.device_name || device.device_type}</span>
                      {device.is_primary && <Badge variant="secondary">{t("profile.primary")}</Badge>}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {device.last_used_at ? formatDateTime(device.last_used_at) : "—"}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
