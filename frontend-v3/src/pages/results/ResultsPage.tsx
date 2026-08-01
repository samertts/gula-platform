import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { resultsApi, limsApi, deviceApi, type LimsResultRow, type LimsReportRow } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input, Button, Select, Dialog, Textarea } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import {
  Search,
  CheckCircle2,
  XCircle,
  Flag,
  Send,
  FileDown,
  Printer,
  FlaskConical,
  Database,
  FileText,
} from "lucide-react";
import { useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { LabResult } from "@/types";
import { formatDateTime, getErrorMessage } from "@/lib/utils";
import { useDebounce } from "@/hooks/useDebounce";

const flagVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  normal: "success",
  high: "warning",
  low: "warning",
  H: "warning",
  L: "warning",
  critical_high: "destructive",
  critical_low: "destructive",
  critical: "destructive",
};

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  verified: "success",
  pending: "warning",
  pending_verification: "warning",
  rejected: "destructive",
  flagged: "warning",
  released: "success",
  validated: "success",
};

interface DeviceTestRow {
  key: string;
  test_name: string;
  value: string;
  unit: string;
  normal_range_low: string;
  normal_range_high: string;
}

export function ResultsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"patient" | "lims" | "reports">("patient");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [category, setCategory] = useState("");
  const [abnormal, setAbnormal] = useState("");
  const [toast, setToast] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["results", debouncedSearch, category, abnormal],
    queryFn: () =>
      resultsApi.list({
        health_id: debouncedSearch || undefined,
        category: category || undefined,
        is_abnormal: abnormal === "yes" ? true : abnormal === "no" ? false : undefined,
        limit: 100,
      }),
  });

  const showToast = (kind: "success" | "error", message: string) => {
    setToast({ kind, message });
    window.setTimeout(() => setToast(null), 4000);
  };

  const verifyMutation = useMutation({
    mutationFn: (id: number) => resultsApi.verify(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["results"] });
      showToast("success", t("result.verified"));
    },
    onError: (err) => showToast("error", getErrorMessage(err)),
  });

  const results = data?.results || data?.items || [];

  const canVerify = (row: LabResult) => !row.verified_at && row.status !== "verified";

  const columns: ColumnDef<LabResult>[] = [
    { accessorKey: "id", header: t("result.id") },
    { accessorKey: "order_id", header: t("result.orderId") },
    { accessorKey: "test_name", header: t("result.testName") },
    {
      accessorKey: "value",
      header: t("result.value"),
      cell: ({ row }) => row.original.value ?? row.original.value_text ?? "-",
    },
    {
      accessorKey: "flag",
      header: t("result.flag"),
      cell: ({ row }) => {
        const flag = row.original.flag;
        return flag ? (
          <Badge variant={flagVariant[flag] || "secondary"}>{flag}</Badge>
        ) : (
          <Badge variant="outline">-</Badge>
        );
      },
    },
    {
      accessorKey: "status",
      header: t("result.status"),
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status || "pending"] || "secondary"}>
          {row.original.status || "pending"}
        </Badge>
      ),
    },
    {
      accessorKey: "created_at",
      header: t("result.createdAt"),
      cell: ({ row }) => formatDateTime(row.original.created_at),
    },
    {
      id: "actions",
      header: t("common.actions"),
      cell: ({ row }) => (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => verifyMutation.mutate(row.original.id)}
            disabled={!canVerify(row.original)}
            title={t("result.verify")}
          >
            <CheckCircle2 className="h-4 w-4" />
            {t("result.verify")}
          </Button>
        </div>
      ),
    },
  ];

  const exportCsv = () => {
    const header = ["id", "order_id", "test_name", "value", "flag", "status", "created_at"];
    const rows = results.map((r) => [r.id, r.order_id, r.test_name, r.value ?? "", r.flag ?? "", r.status ?? "", r.created_at ?? ""]);
    const csv = [header, ...rows].map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `results-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("result.title")}
        description={t("result.subtitle")}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => window.print()} title={t("result.print")}>
              <Printer className="h-4 w-4" />
              {t("result.print")}
            </Button>
            <Button variant="outline" onClick={exportCsv}>
              <FileDown className="h-4 w-4" />
              {t("result.export")}
            </Button>
            <ManualEntryDialog
              onDone={() => {
                queryClient.invalidateQueries({ queryKey: ["results"] });
                showToast("success", t("result.entrySaved"));
              }}
              onError={(msg) => showToast("error", msg)}
            />
          </div>
        }
      />

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

      <div className="flex gap-1 rounded-lg border bg-muted/40 p-1">
        {(
          [
            ["patient", t("result.title"), Database],
            ["lims", t("result.limsWorklist"), FlaskConical],
            ["reports", t("result.reports"), FileText],
          ] as const
        ).map(([key, label, Icon]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              tab === key ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === "patient" && (
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={columns}
              data={results}
              loading={isLoading}
              error={isError ? (error as Error) : null}
              onRetry={() => refetch()}
              toolbar={
                <div className="flex w-full flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="relative">
                      <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        placeholder={t("result.searchHealthId")}
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="ps-9 w-64"
                      />
                    </div>
                    <Select
                      options={[
                        { value: "hematology", label: t("result.category.hematology") },
                        { value: "biochemistry", label: t("result.category.biochemistry") },
                        { value: "immunology", label: t("result.category.immunology") },
                        { value: "microbiology", label: t("result.category.microbiology") },
                        { value: "urinalysis", label: t("result.category.urinalysis") },
                        { value: "coagulation", label: t("result.category.coagulation") },
                      ]}
                      placeholder={t("result.allCategories")}
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      className="w-40"
                    />
                    <Select
                      options={[
                        { value: "yes", label: t("result.abnormalOnly") },
                        { value: "no", label: t("result.normalOnly") },
                      ]}
                      placeholder={t("result.allFlags")}
                      value={abnormal}
                      onChange={(e) => setAbnormal(e.target.value)}
                      className="w-40"
                    />
                  </div>
                </div>
              }
            />
          </CardContent>
        </Card>
      )}

      {tab === "lims" && <LimsWorklist onToast={showToast} />}

      {tab === "reports" && <LimsReports onToast={showToast} />}
    </div>
  );
}

// ── Manual / Analyzer entry ──────────────────────────────────────────────

interface ManualEntryProps {
  onDone: () => void;
  onError: (message: string) => void;
}

function ManualEntryDialog({ onDone, onError }: ManualEntryProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [barcode, setBarcode] = useState("");
  const [deviceId, setDeviceId] = useState("");
  const [rows, setRows] = useState<DeviceTestRow[]>([
    { key: crypto.randomUUID(), test_name: "", value: "", unit: "", normal_range_low: "", normal_range_high: "" },
  ]);

  const mutation = useMutation({
    mutationFn: () =>
      deviceApi.submitResults({
        barcode: barcode.trim(),
        device_id: deviceId.trim() || undefined,
        results: rows
          .filter((r) => r.test_name.trim())
          .map((r) => ({
            test_name: r.test_name.trim(),
            value: r.value === "" ? null : Number(r.value),
            value_text: r.value === "" ? null : r.value,
            unit: r.unit || undefined,
            normal_range_low: r.normal_range_low === "" ? null : Number(r.normal_range_low),
            normal_range_high: r.normal_range_high === "" ? null : Number(r.normal_range_high),
          })),
      }),
    onSuccess: () => {
      setOpen(false);
      setBarcode("");
      setDeviceId("");
      setRows([{ key: crypto.randomUUID(), test_name: "", value: "", unit: "", normal_range_low: "", normal_range_high: "" }]);
      onDone();
    },
    onError: (err) => onError(getErrorMessage(err)),
  });

  const updateRow = (key: string, field: keyof DeviceTestRow, value: string) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, [field]: value } : r)));
  };

  return (
    <>
      <Button onClick={() => setOpen(true)}>
        <FlaskConical className="h-4 w-4" />
        {t("result.manualEntry")}
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={t("result.manualEntry")}
        description={t("result.manualEntryHint")}
        className="max-w-2xl"
        footer={
          <>
            <Button variant="outline" onClick={() => setOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button
              onClick={() => mutation.mutate()}
              loading={mutation.isPending}
              disabled={!barcode.trim() || rows.every((r) => !r.test_name.trim())}
            >
              <Send className="h-4 w-4" />
              {t("result.submitResults")}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">{t("result.barcode")}</label>
              <Input
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                placeholder={t("result.barcodePlaceholder")}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">{t("result.deviceId")}</label>
              <Input value={deviceId} onChange={(e) => setDeviceId(e.target.value)} placeholder={t("result.deviceIdPlaceholder")} />
            </div>
          </div>
          <div className="space-y-2">
            <div className="grid grid-cols-[1fr_1fr_1fr_1fr_1fr_auto] items-center gap-2 text-xs font-medium text-muted-foreground">
              <span>{t("result.testName")}</span>
              <span>{t("result.value")}</span>
              <span>{t("result.unit")}</span>
              <span>{t("result.rangeLow")}</span>
              <span>{t("result.rangeHigh")}</span>
              <span />
            </div>
            {rows.map((row) => (
              <div key={row.key} className="grid grid-cols-[1fr_1fr_1fr_1fr_1fr_auto] items-center gap-2">
                <Input value={row.test_name} onChange={(e) => updateRow(row.key, "test_name", e.target.value)} placeholder={t("result.testName")} />
                <Input value={row.value} onChange={(e) => updateRow(row.key, "value", e.target.value)} placeholder="—" inputMode="decimal" />
                <Input value={row.unit} onChange={(e) => updateRow(row.key, "unit", e.target.value)} placeholder={t("result.unit")} />
                <Input value={row.normal_range_low} onChange={(e) => updateRow(row.key, "normal_range_low", e.target.value)} placeholder="—" inputMode="decimal" />
                <Input value={row.normal_range_high} onChange={(e) => updateRow(row.key, "normal_range_high", e.target.value)} placeholder="—" inputMode="decimal" />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setRows((prev) => prev.filter((r) => r.key !== row.key))}
                  disabled={rows.length === 1}
                >
                  <XCircle className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                setRows((prev) => [
                  ...prev,
                  { key: crypto.randomUUID(), test_name: "", value: "", unit: "", normal_range_low: "", normal_range_high: "" },
                ])
              }
            >
              {t("order.addTest")}
            </Button>
          </div>
        </div>
      </Dialog>
    </>
  );
}

// ── LIMS worklist (validation lifecycle) ─────────────────────────────────

function LimsWorklist({ onToast }: { onToast: (kind: "success" | "error", message: string) => void }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [validationStatus, setValidationStatus] = useState("");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["lims-results", validationStatus],
    queryFn: () => limsApi.listResults({ validation_status: validationStatus || undefined, limit: 100 }),
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["lims-results"] });
  };

  const actionMutation = useMutation({
    mutationFn: ({ id, action, notes }: { id: number; action: "validate" | "reject" | "flag"; notes?: string }) =>
      limsApi.validateResult(id, { action, notes }),
    onSuccess: () => {
      refresh();
      onToast("success", t("result.statusUpdated"));
    },
    onError: (err) => onToast("error", getErrorMessage(err)),
  });

  const releaseMutation = useMutation({
    mutationFn: (id: number) => limsApi.releaseResult(id),
    onSuccess: () => {
      refresh();
      onToast("success", t("result.released"));
    },
    onError: (err) => onToast("error", getErrorMessage(err)),
  });

  const limsResults = data?.results || [];

  const limsColumns: ColumnDef<LimsResultRow>[] = [
    { accessorKey: "id", header: t("result.id") },
    { accessorKey: "specimen_id", header: t("result.specimen") },
    { accessorKey: "test_code", header: t("result.testCode") },
    { accessorKey: "test_name", header: t("result.testName") },
    {
      accessorKey: "value",
      header: t("result.value"),
      cell: ({ row }) => row.original.value_numeric ?? row.original.value_text ?? "-",
    },
    {
      accessorKey: "validation_status",
      header: t("result.validationStatus"),
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.validation_status || "pending"] || "secondary"}>
          {row.original.validation_status || "pending"}
        </Badge>
      ),
    },
    {
      accessorKey: "created_at",
      header: t("result.createdAt"),
      cell: ({ row }) => formatDateTime(row.original.created_at),
    },
    {
      id: "actions",
      header: t("common.actions"),
      cell: ({ row }) => (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => actionMutation.mutate({ id: row.original.id, action: "validate" })}
            disabled={["validated", "released"].includes(row.original.validation_status)}
            title={t("result.validate")}
          >
            <CheckCircle2 className="h-4 w-4" />
            {t("result.validate")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => actionMutation.mutate({ id: row.original.id, action: "reject" })}
            disabled={["released"].includes(row.original.validation_status)}
            title={t("result.reject")}
          >
            <XCircle className="h-4 w-4" />
            {t("result.reject")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => actionMutation.mutate({ id: row.original.id, action: "flag" })}
            disabled={["released"].includes(row.original.validation_status)}
            title={t("result.flagAction")}
          >
            <Flag className="h-4 w-4" />
            {t("result.flagAction")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => releaseMutation.mutate(row.original.id)}
            disabled={row.original.validation_status !== "validated"}
            title={t("result.release")}
          >
            <Send className="h-4 w-4" />
            {t("result.release")}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <Card>
      <CardContent className="pt-6">
        <DataTable
          columns={limsColumns}
          data={limsResults}
          loading={isLoading}
          error={isError ? (error as Error) : null}
          onRetry={() => refetch()}
          toolbar={
            <div className="flex w-full items-center gap-2">
              <Select
                options={[
                  { value: "pending", label: t("result.vs.pending") },
                  { value: "validated", label: t("result.vs.validated") },
                  { value: "rejected", label: t("result.vs.rejected") },
                  { value: "flagged", label: t("result.vs.flagged") },
                  { value: "released", label: t("result.vs.released") },
                ]}
                placeholder={t("result.allStatuses")}
                value={validationStatus}
                onChange={(e) => setValidationStatus(e.target.value)}
                className="w-44"
              />
            </div>
          }
        />
      </CardContent>
    </Card>
  );
}

// ── LIMS reports (finalize / correct) ────────────────────────────────────

function LimsReports({ onToast }: { onToast: (kind: "success" | "error", message: string) => void }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("");
  const [generateOpen, setGenerateOpen] = useState(false);
  const [orderId, setOrderId] = useState("");
  const [reportNumber, setReportNumber] = useState("");
  const [correcting, setCorrecting] = useState<LimsReportRow | null>(null);
  const [correctReason, setCorrectReason] = useState("");
  const [correctDetails, setCorrectDetails] = useState("");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["lims-reports", status],
    queryFn: () => limsApi.reports({ status: status || undefined, limit: 100 }),
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["lims-reports"] });

  const generateMutation = useMutation({
    mutationFn: () =>
      limsApi.generateReport({
        order_id: Number(orderId),
        report_number: reportNumber.trim(),
        locale: "ar",
      }),
    onSuccess: () => {
      setGenerateOpen(false);
      setOrderId("");
      setReportNumber("");
      refresh();
      onToast("success", t("result.reportGenerated"));
    },
    onError: (err) => onToast("error", getErrorMessage(err)),
  });

  const finalizeMutation = useMutation({
    mutationFn: (reportId: number) => limsApi.finalizeReport(reportId),
    onSuccess: () => {
      refresh();
      onToast("success", t("result.reportFinalized"));
    },
    onError: (err) => onToast("error", getErrorMessage(err)),
  });

  const correctMutation = useMutation({
    mutationFn: () => limsApi.correctReport(correcting!.id, { reason: correctReason.trim(), corrections: correctDetails.trim() }),
    onSuccess: () => {
      setCorrecting(null);
      setCorrectReason("");
      setCorrectDetails("");
      refresh();
      onToast("success", t("result.reportCorrected"));
    },
    onError: (err) => onToast("error", getErrorMessage(err)),
  });

  const reports = data?.reports || [];

  const reportColumns: ColumnDef<LimsReportRow>[] = [
    { accessorKey: "id", header: t("result.id") },
    { accessorKey: "report_number", header: t("result.reportNumber") },
    { accessorKey: "order_id", header: t("result.orderId") },
    {
      accessorKey: "status",
      header: t("result.status"),
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status || "draft"] || "secondary"}>{row.original.status || "draft"}</Badge>
      ),
    },
    {
      accessorKey: "created_at",
      header: t("result.createdAt"),
      cell: ({ row }) => formatDateTime(row.original.created_at),
    },
    {
      id: "actions",
      header: t("common.actions"),
      cell: ({ row }) => (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => finalizeMutation.mutate(row.original.id)}
            disabled={row.original.status === "finalized"}
            title={t("result.finalize")}
          >
            <CheckCircle2 className="h-4 w-4" />
            {t("result.finalize")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setCorrecting(row.original);
              setCorrectReason("");
              setCorrectDetails("");
            }}
            disabled={row.original.status === "corrected"}
            title={t("result.correct")}
          >
            {t("result.correct")}
          </Button>
        </div>
      ),
    },
  ];

  return (
    <Card>
      <CardContent className="pt-6">
        <DataTable
          columns={reportColumns}
          data={reports}
          loading={isLoading}
          error={isError ? (error as Error) : null}
          onRetry={() => refetch()}
          toolbar={
            <div className="flex w-full items-center gap-2">
              <Select
                options={[
                  { value: "draft", label: t("result.vs.pending") },
                  { value: "finalized", label: t("result.vs.released") },
                  { value: "corrected", label: t("result.corrected") },
                ]}
                placeholder={t("result.allStatuses")}
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-44"
              />
              <Button onClick={() => setGenerateOpen(true)}>
                <FileText className="h-4 w-4" />
                {t("result.generateReport")}
              </Button>
            </div>
          }
        />
      </CardContent>

      <Dialog
        open={generateOpen}
        onClose={() => setGenerateOpen(false)}
        title={t("result.generateReport")}
        className="max-w-md"
        footer={
          <>
            <Button variant="outline" onClick={() => setGenerateOpen(false)}>
              {t("common.cancel")}
            </Button>
            <Button
              onClick={() => generateMutation.mutate()}
              loading={generateMutation.isPending}
              disabled={!orderId.trim() || !reportNumber.trim()}
            >
              {t("result.generateReport")}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("result.orderId")}</label>
            <Input value={orderId} onChange={(e) => setOrderId(e.target.value)} inputMode="numeric" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("result.reportNumber")}</label>
            <Input value={reportNumber} onChange={(e) => setReportNumber(e.target.value)} />
          </div>
        </div>
      </Dialog>

      <Dialog
        open={correcting !== null}
        onClose={() => setCorrecting(null)}
        title={t("result.correctReport")}
        className="max-w-md"
        footer={
          <>
            <Button variant="outline" onClick={() => setCorrecting(null)}>
              {t("common.cancel")}
            </Button>
            <Button onClick={() => correctMutation.mutate()} loading={correctMutation.isPending} disabled={!correctReason.trim()}>
              {t("result.correct")}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("result.correctReason")}</label>
            <Input value={correctReason} onChange={(e) => setCorrectReason(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("result.correctDetails")}</label>
            <Textarea value={correctDetails} onChange={(e) => setCorrectDetails(e.target.value)} rows={3} />
          </div>
        </div>
      </Dialog>
    </Card>
  );
}
