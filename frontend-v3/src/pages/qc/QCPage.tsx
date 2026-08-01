import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { qcApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Button, Dialog, Input, Select, Textarea } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import type { ColumnDef } from "@tanstack/react-table";
import type { QualityControl } from "@/types";
import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { formatDateTime, getErrorMessage } from "@/lib/utils";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  passed: "success",
  failed: "destructive",
  warning: "warning",
  pending: "secondary",
};

const LEVELS = ["low", "normal", "high", "level1", "level2", "level3"];

export function QCPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [toast, setToast] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["qc"],
    queryFn: () => qcApi.list({ limit: 100 }),
  });

  const { data: summary } = useQuery({
    queryKey: ["qc-summary"],
    queryFn: () => qcApi.summary({ days: 30 }),
  });

  const showToast = (kind: "success" | "error", message: string) => {
    setToast({ kind, message });
    window.setTimeout(() => setToast(null), 4000);
  };

  const submitMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => qcApi.submit(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["qc"] });
      queryClient.invalidateQueries({ queryKey: ["qc-summary"] });
      showToast("success", t("qc.submitted"));
    },
    onError: (err) => showToast("error", getErrorMessage(err)),
  });

  const items = (data as { qc_results?: QualityControl[] } | undefined)?.qc_results || [];

  const columns: ColumnDef<QualityControl>[] = [
    { accessorKey: "test_code", header: t("qc.testCode") },
    { accessorKey: "level", header: t("qc.level") },
    {
      accessorKey: "measured_value",
      header: t("qc.measured"),
      cell: ({ row }) => `${row.original.measured_value}${row.original.unit ? ` ${row.original.unit}` : ""}`,
    },
    { accessorKey: "expected_value", header: t("qc.expected") },
    {
      accessorKey: "status",
      header: t("qc.status"),
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"}>
          {row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: "violation",
      header: t("qc.violation"),
      cell: ({ row }) => row.original.violation || "—",
    },
    {
      accessorKey: "created_at",
      header: t("qc.createdAt"),
      cell: ({ row }) => formatDateTime(row.original.created_at),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("qc.title")} description={t("qc.subtitle")} />

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

      {summary && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard label={t("qc.totalTests")} value={summary.total_tests} />
          <SummaryCard label={t("qc.passed")} value={summary.passed} tone="success" />
          <SummaryCard label={t("qc.warningCount")} value={summary.warning} tone="warning" />
          <SummaryCard
            label={t("qc.passRate")}
            value={`${summary.pass_rate_pct.toFixed(1)}%`}
            tone={summary.pass_rate_pct >= 95 ? "success" : "destructive"}
          />
        </div>
      )}

      <Card>
        <CardContent className="pt-6">
          <DataTable
            columns={columns}
            data={items}
            loading={isLoading}
            error={isError ? (error as Error) : null}
            onRetry={() => refetch()}
            toolbar={
              <div className="flex w-full items-center justify-end">
                <Button onClick={() => setCreateOpen(true)}>
                  <Plus className="h-4 w-4" />
                  {t("qc.newEntry")}
                </Button>
              </div>
            }
          />
        </CardContent>
      </Card>

      <QcEntryDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSubmit={(data) => submitMutation.mutate(data)}
        loading={submitMutation.isPending}
      />
    </div>
  );
}

function SummaryCard({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number | string;
  tone?: "default" | "success" | "warning" | "destructive";
}) {
  const tones: Record<string, string> = {
    default: "text-foreground",
    success: "text-green-600 dark:text-green-400",
    warning: "text-yellow-600 dark:text-yellow-400",
    destructive: "text-red-600 dark:text-red-400",
  };
  return (
    <Card>
      <CardContent className="p-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className={`mt-1 text-2xl font-bold ${tones[tone]}`}>{value}</p>
      </CardContent>
    </Card>
  );
}

function QcEntryDialog({
  open,
  onClose,
  onSubmit,
  loading,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: Record<string, unknown>) => void;
  loading: boolean;
}) {
  const { t } = useTranslation();
  const [testCode, setTestCode] = useState("");
  const [level, setLevel] = useState("");
  const [expected, setExpected] = useState("");
  const [measured, setMeasured] = useState("");
  const [sd, setSd] = useState("");
  const [unit, setUnit] = useState("");
  const [instrument, setInstrument] = useState("");
  const [lotNumber, setLotNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setTestCode("");
    setLevel("");
    setExpected("");
    setMeasured("");
    setSd("");
    setUnit("");
    setInstrument("");
    setLotNumber("");
    setNotes("");
    setError("");
  }, [open]);

  const handleSubmit = () => {
    setError("");
    if (!testCode.trim()) {
      setError(t("validation.required"));
      return;
    }
    if (!level) {
      setError(t("validation.required"));
      return;
    }
    if (expected === "" || measured === "") {
      setError(t("validation.required"));
      return;
    }
    const payload: Record<string, unknown> = {
      test_code: testCode.trim(),
      level,
      expected_value: Number(expected),
      measured_value: Number(measured),
      unit: unit || undefined,
      instrument_name: instrument || undefined,
      lot_number: lotNumber || undefined,
      notes: notes || undefined,
    };
    if (sd !== "") payload.sd = Number(sd);
    onSubmit(payload);
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={t("qc.newEntry")}
      description={t("qc.newEntryDesc")}
      className="max-w-xl"
      footer={
        <>
          <Button variant="outline" onClick={onClose}>{t("common.cancel")}</Button>
          <Button onClick={handleSubmit} loading={loading}>{t("common.submit")}</Button>
        </>
      }
    >
      <div className="space-y-4">
        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("qc.testCode")} *</label>
            <Input value={testCode} onChange={(e) => setTestCode(e.target.value)} dir="ltr" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("qc.level")} *</label>
            <Select
              options={LEVELS.map((l) => ({ value: l, label: l }))}
              placeholder={t("common.select")}
              value={level}
              onChange={(e) => setLevel(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("qc.expected")} *</label>
            <Input type="number" value={expected} onChange={(e) => setExpected(e.target.value)} dir="ltr" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("qc.measured")} *</label>
            <Input type="number" value={measured} onChange={(e) => setMeasured(e.target.value)} dir="ltr" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("qc.sd")}</label>
            <Input type="number" value={sd} onChange={(e) => setSd(e.target.value)} dir="ltr" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("qc.unit")}</label>
            <Input value={unit} onChange={(e) => setUnit(e.target.value)} dir="ltr" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("qc.instrument")}</label>
            <Input value={instrument} onChange={(e) => setInstrument(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("qc.lotNumber")}</label>
            <Input value={lotNumber} onChange={(e) => setLotNumber(e.target.value)} />
          </div>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("qc.notes")}</label>
          <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
      </div>
    </Dialog>
  );
}
