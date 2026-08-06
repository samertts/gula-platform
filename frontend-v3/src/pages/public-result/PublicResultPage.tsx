import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useParams, Link } from "react-router";
import { publicResultsApi } from "@/api/endpoints";
import { Card, CardContent, Badge, Button } from "@/components/ui";
import { LoadingSpinner } from "@/components/shared/PageComponents";
import { FileDown, FlaskConical } from "lucide-react";
import type { LabResult } from "@/types";
import { formatDateTime, downloadBlob, getErrorMessage } from "@/lib/utils";
import { useState } from "react";

const flagVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  normal: "success",
  high: "warning",
  low: "warning",
  H: "warning",
  L: "warning",
  critical: "destructive",
  critical_high: "destructive",
  critical_low: "destructive",
};

export function PublicResultPage() {
  const { token } = useParams<{ token: string }>();
  const { t } = useTranslation();
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  const { data, isLoading, isError, error: queryError, refetch } = useQuery({
    queryKey: ["public-result", token],
    queryFn: () => publicResultsApi.get(token as string),
    enabled: !!token,
  });

  const handleDownload = async () => {
    if (!token) return;
    setDownloading(true);
    setError("");
    try {
      const blob = await publicResultsApi.downloadPdf(token);
      downloadBlob(blob, `result-${token.slice(0, 8)}.pdf`);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDownloading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background p-6">
        <FlaskConical className="h-12 w-12 text-muted-foreground" />
        <h1 className="text-xl font-bold">{t("publicResult.notFound")}</h1>
        <p className="text-sm text-muted-foreground">{getErrorMessage(queryError, t("publicResult.expired"))}</p>
        <Button variant="outline" onClick={() => refetch()}>{t("common.retry")}</Button>
        <Link to="/login" className="text-sm text-primary hover:underline">
          {t("publicResult.loginLink")}
        </Link>
      </div>
    );
  }

  const results: LabResult[] = data.results || [];

  return (
    <div className="min-h-screen bg-muted/30 p-4 sm:p-8">
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-center justify-center gap-2 text-primary">
          <FlaskConical className="h-8 w-8" />
          <span className="text-xl font-bold">{t("app.name")}</span>
        </div>

        <Card>
          <CardContent className="space-y-4 p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h1 className="text-xl font-bold">{t("publicResult.title")}</h1>
                <p className="text-sm text-muted-foreground">{t("publicResult.subtitle")}</p>
              </div>
              <Button onClick={handleDownload} loading={downloading} variant="outline">
                <FileDown className="h-4 w-4" />
                {t("publicResult.downloadPdf")}
              </Button>
            </div>

            {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

            <div className="grid gap-2 sm:grid-cols-2">
              <InfoRow label={t("publicResult.patientName")} value={data.patient?.full_name} />
              <InfoRow label={t("patient.healthId")} value={data.patient?.health_id} />
              <InfoRow label={t("publicResult.issuedAt")} value={results[0] ? formatDateTime(results[0].created_at) : "—"} />
              <InfoRow label={t("publicResult.testsCount")} value={results.length} />
            </div>

            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50 text-muted-foreground">
                    <th className="px-3 py-2 text-start font-medium">{t("publicResult.testName")}</th>
                    <th className="px-3 py-2 text-start font-medium">{t("publicResult.value")}</th>
                    <th className="px-3 py-2 text-start font-medium">{t("publicResult.normalRange")}</th>
                    <th className="px-3 py-2 text-start font-medium">{t("publicResult.flag")}</th>
                  </tr>
                </thead>
                <tbody>
                  {results.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-3 py-6 text-center text-muted-foreground">
                        {t("publicResult.empty")}
                      </td>
                    </tr>
                  )}
                  {results.map((r) => (
                    <tr key={r.id ?? r.test_name} className="border-b">
                      <td className="px-3 py-2">{r.test_name}</td>
                      <td className="px-3 py-2">{r.value ?? r.value_text ?? "—"}</td>
                      <td className="px-3 py-2">
                        {r.normal_range_low != null && r.normal_range_high != null
                          ? `${r.normal_range_low} — ${r.normal_range_high} ${r.unit || ""}`
                          : "—"}
                      </td>
                      <td className="px-3 py-2">
                        {r.flag ? <Badge variant={flagVariant[r.flag] || "secondary"}>{r.flag}</Badge> : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="text-center text-xs text-muted-foreground">{t("publicResult.disclaimer")}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <div className="rounded-md border bg-muted/30 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value ?? "—"}</p>
    </div>
  );
}
