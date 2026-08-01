import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ordersApi, patientsApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input, Button, Dialog } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Search, Plus, Eye, CheckCircle2, XCircle, BrainCircuit, Loader2 } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { LabOrder, Patient } from "@/types";
import { formatDate, formatDateTime, getErrorMessage } from "@/lib/utils";
import { useDebounce } from "@/hooks/useDebounce";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  pending: "warning",
  completed: "success",
  validated: "default",
  cancelled: "destructive",
  in_progress: "secondary",
};

interface TestRow {
  key: string;
  test_name: string;
  value: string;
  value_text: string;
  unit: string;
  normal_range_low: string;
  normal_range_high: string;
}

interface IntelligenceResult {
  patterns_detected: number;
  patterns: { name: string; description: string; severity: string }[];
  flag_summary: { total: number; flags: Record<string, number> };
  has_critical_pattern: boolean;
}

export function OrdersPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [createOpen, setCreateOpen] = useState(false);
  const [detailOrder, setDetailOrder] = useState<LabOrder | null>(null);
  const [toast, setToast] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["orders", debouncedSearch],
    queryFn: () => ordersApi.list({ search: debouncedSearch || undefined, limit: 100 }),
  });

  const showToast = useCallback((kind: "success" | "error", message: string) => {
    setToast({ kind, message });
    window.setTimeout(() => setToast(null), 4000);
  }, []);

  const validateMutation = useMutation({
    mutationFn: (id: number) => ordersApi.validate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["order", detailOrder?.id] });
      showToast("success", t("order.validatedSuccess"));
      setDetailOrder(null);
    },
    onError: (err) => showToast("error", getErrorMessage(err)),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => ordersApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      showToast("success", t("order.cancelledSuccess"));
      setDetailOrder(null);
    },
    onError: (err) => showToast("error", getErrorMessage(err)),
  });

  const analyzeMutation = useMutation({
    mutationFn: (id: number) => ordersApi.analyze(id),
    onSuccess: (data) => {
      const result = data as unknown as IntelligenceResult;
      const patternSummary = result.patterns?.length
        ? result.patterns.map((p) => `• ${p.name} (${p.severity})`).join("\n")
        : t("order.noPatterns");
      showToast(
        result.has_critical_pattern ? "error" : "success",
        `${t("order.intelligenceDone")} — ${patternSummary}`,
      );
    },
    onError: (err) => showToast("error", getErrorMessage(err)),
  });

  const columns: ColumnDef<LabOrder>[] = useMemo(
    () => [
      { accessorKey: "id", header: t("order.orderId"), cell: ({ row }) => `#${row.original.id}` },
      { accessorKey: "patient_name", header: t("order.patientName") },
      { accessorKey: "doctor_name", header: t("order.doctorName"), cell: ({ row }) => row.original.doctor_name || "—" },
      {
        accessorKey: "status",
        header: t("order.status"),
        cell: ({ row }) => (
          <Badge variant={statusVariant[row.original.status] || "secondary"}>
            {row.original.status}
          </Badge>
        ),
      },
      {
        accessorKey: "results_count",
        header: t("order.testsCount"),
        cell: ({ row }) => row.original.results_count ?? row.original.results?.length ?? "-",
      },
      {
        accessorKey: "created_at",
        header: t("order.createdAt"),
        cell: ({ row }) => formatDate(row.original.created_at),
      },
      {
        id: "actions",
        header: t("common.actions"),
        cell: ({ row }) => (
          <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="icon" title={t("common.view")} onClick={() => setDetailOrder(row.original)}>
              <Eye className="h-4 w-4" />
            </Button>
          </div>
        ),
      },
    ],
    [t],
  );

  return (
    <div className="space-y-6">
      <PageHeader title={t("order.title")} description={t("order.subtitle")} />

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

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={data || []}
            loading={isLoading}
            error={isError ? (error as Error) : null}
            onRetry={() => refetch()}
            onRowClick={(row) => setDetailOrder(row)}
            toolbar={
              <div className="flex w-full flex-wrap items-center justify-between gap-3">
                <div className="relative">
                  <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder={t("order.search")}
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="ps-9 w-80"
                  />
                </div>
                <Button onClick={() => setCreateOpen(true)}>
                  <Plus className="h-4 w-4" />
                  {t("order.newOrder")}
                </Button>
              </div>
            }
          />
        </CardContent>
      </Card>

      <CreateOrderDialog open={createOpen} onClose={() => setCreateOpen(false)} onCreated={() => showToast("success", t("order.created"))} />

      <OrderDetailDialog
        order={detailOrder}
        onClose={() => setDetailOrder(null)}
        onValidate={(id) => validateMutation.mutate(id)}
        onCancel={(id) => cancelMutation.mutate(id)}
        onAnalyze={(id) => analyzeMutation.mutate(id)}
        analyzing={analyzeMutation.isPending}
      />
    </div>
  );
}

function CreateOrderDialog({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: () => void }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [patientSearch, setPatientSearch] = useState("");
  const debouncedPatientSearch = useDebounce(patientSearch, 300);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [doctorName, setDoctorName] = useState("");
  const [tests, setTests] = useState<TestRow[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { data: patients } = useQuery({
    queryKey: ["patients-search", debouncedPatientSearch],
    queryFn: () => patientsApi.list({ search: debouncedPatientSearch || undefined, limit: 8 }),
    enabled: open,
  });

  const { data: profiles } = useQuery({
    queryKey: ["test-profiles"],
    queryFn: () => ordersApi.testProfiles(),
    enabled: open,
  });

  const addEmptyTest = () => {
    setTests((prev) => [
      ...prev,
      { key: crypto.randomUUID(), test_name: "", value: "", value_text: "", unit: "", normal_range_low: "", normal_range_high: "" },
    ]);
  };

  const addProfile = (profileName: string) => {
    const profile = profiles?.[profileName];
    if (!profile) return;
    setTests((prev) => [
      ...prev,
      ...profile.map((p, i) => ({
        key: `${profileName}-${i}-${crypto.randomUUID()}`,
        test_name: p.test_name,
        value: "",
        value_text: "",
        unit: p.unit || "",
        normal_range_low: p.normal_range_low != null ? String(p.normal_range_low) : "",
        normal_range_high: p.normal_range_high != null ? String(p.normal_range_high) : "",
      })),
    ]);
  };

  const updateTest = (key: string, field: keyof TestRow, value: string) => {
    setTests((prev) => prev.map((row) => (row.key === key ? { ...row, [field]: value } : row)));
  };

  const removeTest = (key: string) => {
    setTests((prev) => prev.filter((row) => row.key !== key));
  };

  const handleSubmit = async () => {
    setError("");
    if (!patient) {
      setError(t("order.selectPatient"));
      return;
    }
    if (tests.length === 0 || tests.some((row) => !row.test_name.trim())) {
      setError(t("order.addTest"));
      return;
    }
    setLoading(true);
    try {
      await ordersApi.create({
        patient_id: patient.id,
        doctor_name: doctorName.trim() || undefined,
        results: tests.map((row) => ({
          test_name: row.test_name.trim(),
          value: row.value ? Number(row.value) : null,
          value_text: row.value_text || undefined,
          unit: row.unit || undefined,
          normal_range_low: row.normal_range_low ? Number(row.normal_range_low) : undefined,
          normal_range_high: row.normal_range_high ? Number(row.normal_range_high) : undefined,
        })),
      });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      onCreated();
      setPatient(null);
      setPatientSearch("");
      setDoctorName("");
      setTests([]);
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const patientOptions = ((patients as { patients?: Patient[] } | undefined)?.patients || []).map((p) => ({
    value: String(p.id),
    label: `${p.full_name} — ${p.health_id || p.phone}`,
  }));

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={t("order.newOrder")}
      description={t("order.newOrderDesc")}
      className="max-w-2xl"
      footer={
        <>
          <Button variant="outline" onClick={onClose}>{t("common.cancel")}</Button>
          <Button onClick={handleSubmit} loading={loading}>{t("common.create")}</Button>
        </>
      }
    >
      <div className="space-y-4">
        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}

        <div className="space-y-2">
          <label className="text-sm font-medium">{t("order.patient")}</label>
          <Input
            placeholder={t("order.searchPatient")}
            value={patientSearch}
            onChange={(e) => setPatientSearch(e.target.value)}
          />
          {!patient && patientOptions.length > 0 && (
            <div className="max-h-40 overflow-y-auto rounded-md border">
              {patientOptions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  className="block w-full px-3 py-2 text-start text-sm hover:bg-accent"
                  onClick={() => {
                    const p = ((patients as { patients?: Patient[] } | undefined)?.patients || []).find(
                      (x) => String(x.id) === opt.value,
                    );
                    if (p) setPatient(p);
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
          {patient && (
            <div className="flex items-center justify-between rounded-md border bg-muted/50 px-3 py-2 text-sm">
              <span>
                {patient.full_name} — {patient.health_id || patient.phone}
              </span>
              <Button variant="ghost" size="sm" onClick={() => setPatient(null)}>{t("common.clear")}</Button>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">{t("order.doctorName")}</label>
          <Input value={doctorName} onChange={(e) => setDoctorName(e.target.value)} />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">{t("order.tests")}</label>
            <Button variant="outline" size="sm" onClick={addEmptyTest}>
              <Plus className="h-3 w-3" /> {t("order.addTest")}
            </Button>
          </div>

          {profiles && Object.keys(profiles).length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-muted-foreground">{t("order.profiles")}:</span>
              {Object.keys(profiles).map((name) => (
                <Button key={name} type="button" variant="secondary" size="sm" onClick={() => addProfile(name)}>
                  {name}
                </Button>
              ))}
            </div>
          )}

          {tests.length === 0 && (
            <p className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
              {t("order.noTests")}
            </p>
          )}

          {tests.map((row) => (
            <div key={row.key} className="space-y-2 rounded-md border p-3">
              <div className="grid gap-2 sm:grid-cols-2">
                <Input
                  placeholder={t("order.testName")}
                  value={row.test_name}
                  onChange={(e) => updateTest(row.key, "test_name", e.target.value)}
                />
                <div className="flex items-center gap-2">
                  <Input
                    placeholder={t("order.value")}
                    value={row.value}
                    onChange={(e) => updateTest(row.key, "value", e.target.value)}
                    className="flex-1"
                  />
                  <Button variant="ghost" size="icon" onClick={() => removeTest(row.key)} title={t("common.delete")}>
                    <XCircle className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="grid gap-2 sm:grid-cols-3">
                <Input
                  placeholder={t("order.unit")}
                  value={row.unit}
                  onChange={(e) => updateTest(row.key, "unit", e.target.value)}
                />
                <Input
                  placeholder={t("order.normalLow")}
                  value={row.normal_range_low}
                  onChange={(e) => updateTest(row.key, "normal_range_low", e.target.value)}
                />
                <Input
                  placeholder={t("order.normalHigh")}
                  value={row.normal_range_high}
                  onChange={(e) => updateTest(row.key, "normal_range_high", e.target.value)}
                />
              </div>
              <Input
                placeholder={t("order.valueText")}
                value={row.value_text}
                onChange={(e) => updateTest(row.key, "value_text", e.target.value)}
              />
            </div>
          ))}
        </div>
      </div>
    </Dialog>
  );
}

function OrderDetailDialog({
  order,
  onClose,
  onValidate,
  onCancel,
  onAnalyze,
  analyzing,
}: {
  order: LabOrder | null;
  onClose: () => void;
  onValidate: (id: number) => void;
  onCancel: (id: number) => void;
  onAnalyze: (id: number) => void;
  analyzing: boolean;
}) {
  const { t } = useTranslation();
  const orderId = order?.id;

  const { data: detail, isLoading } = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => ordersApi.get(orderId as number),
    enabled: !!orderId,
  });

  const orderData = detail || order;
  const isLocked = !!orderData?.locked_at || orderData?.status === "validated";
  const isCancelled = orderData?.status === "cancelled";

  return (
    <Dialog
      open={!!order}
      onClose={onClose}
      title={t("order.details")}
      description={orderData ? `${orderData.patient_name || ""} — ${formatDateTime(orderData.created_at)}` : undefined}
      className="max-w-2xl"
      footer={
        <div className="flex flex-wrap items-center gap-2">
          {!isLocked && !isCancelled && (
            <>
              <Button onClick={() => orderId && onValidate(orderId)}>
                <CheckCircle2 className="h-4 w-4" /> {t("order.validate")}
              </Button>
              <Button variant="destructive" onClick={() => orderId && onCancel(orderId)}>
                <XCircle className="h-4 w-4" /> {t("order.cancel")}
              </Button>
            </>
          )}
          <Button variant="outline" onClick={() => orderId && onAnalyze(orderId)} disabled={analyzing}>
            {analyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : <BrainCircuit className="h-4 w-4" />}
            {t("order.analyzeIntelligence")}
          </Button>
        </div>
      }
    >
      {isLoading && !orderData?.results ? (
        <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">{t("common.loading")}</div>
      ) : (
        <div className="space-y-4">
          <div className="grid gap-2 sm:grid-cols-2">
            <InfoRow label={t("order.orderId")} value={orderData?.id} />
            <InfoRow label={t("order.status")} value={orderData?.status} />
            <InfoRow label={t("order.patientName")} value={orderData?.patient_name} />
            <InfoRow label={t("order.doctorName")} value={orderData?.doctor_name || "—"} />
            <InfoRow label={t("order.createdAt")} value={formatDateTime(orderData?.created_at)} />
            <InfoRow label={t("order.validatedAt")} value={formatDateTime(orderData?.validated_at)} />
          </div>

          <div>
            <h3 className="mb-2 text-sm font-semibold">{t("order.results")}</h3>
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50 text-muted-foreground">
                    <th className="px-3 py-2 text-start font-medium">{t("order.testName")}</th>
                    <th className="px-3 py-2 text-start font-medium">{t("order.value")}</th>
                    <th className="px-3 py-2 text-start font-medium">{t("order.normalRange")}</th>
                    <th className="px-3 py-2 text-start font-medium">{t("order.status")}</th>
                  </tr>
                </thead>
                <tbody>
                  {(orderData?.results || []).length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-3 py-4 text-center text-muted-foreground">
                        {t("order.noResults")}
                      </td>
                    </tr>
                  )}
                  {(orderData?.results || []).map((r) => (
                    <tr key={r.id} className="border-b">
                      <td className="px-3 py-2">{r.test_name}</td>
                      <td className="px-3 py-2">{r.value ?? r.value_text ?? "—"}</td>
                      <td className="px-3 py-2">
                        {r.normal_range_low != null && r.normal_range_high != null
                          ? `${r.normal_range_low} — ${r.normal_range_high}`
                          : "—"}
                      </td>
                      <td className="px-3 py-2">
                        {r.flag ? <Badge variant={statusVariant[r.flag] || "secondary"}>{r.flag}</Badge> : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </Dialog>
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
