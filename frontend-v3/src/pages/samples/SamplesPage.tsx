import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { samplesApi, ordersApi } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Input, Button, Dialog, Select, Textarea } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Search, Plus, ArrowRight, Copy } from "lucide-react";
import { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Sample } from "@/types";
import { formatDateTime, getErrorMessage } from "@/lib/utils";
import { useDebounce } from "@/hooks/useDebounce";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  collected: "secondary",
  received: "default",
  processing: "warning",
  analyzed: "success",
  rejected: "destructive",
};

const SAMPLE_TYPES = ["blood", "urine", "stool", "swab", "serum", "plasma", "csf", "sputum", "other"];
const STATUS_TRANSITIONS: Record<string, string[]> = {
  collected: ["received", "rejected"],
  received: ["processing", "rejected"],
  processing: ["analyzed", "rejected"],
  analyzed: [],
  rejected: [],
};

export function SamplesPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [createOpen, setCreateOpen] = useState(false);
  const [selected, setSelected] = useState<Sample | null>(null);
  const [toast, setToast] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["samples", debouncedSearch],
    queryFn: () => samplesApi.list({ limit: 100 }),
  });

  const samples = (data as { samples?: Sample[] } | undefined)?.samples || [];

  const showToast = (kind: "success" | "error", message: string) => {
    setToast({ kind, message });
    window.setTimeout(() => setToast(null), 4000);
  };

  const statusMutation = useMutation({
    mutationFn: ({ barcode, status, rejection_reason }: { barcode: string; status: string; rejection_reason?: string }) =>
      samplesApi.update(barcode, { status, rejection_reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["samples"] });
      showToast("success", t("sample.statusUpdated"));
      setSelected(null);
    },
    onError: (err) => showToast("error", getErrorMessage(err)),
  });

  const columns: ColumnDef<Sample>[] = [
    { accessorKey: "barcode", header: t("sample.barcode") },
    { accessorKey: "sample_type", header: t("sample.sampleType") },
    {
      accessorKey: "status",
      header: t("sample.status"),
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"}>
          {row.original.status}
        </Badge>
      ),
    },
    {
      accessorKey: "created_at",
      header: t("sample.collectionTime"),
      cell: ({ row }) => formatDateTime(row.original.created_at),
    },
    { accessorKey: "notes", header: t("sample.notes"), cell: ({ row }) => row.original.notes || "—" },
    {
      id: "actions",
      header: t("common.actions"),
      cell: ({ row }) => (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="icon"
            title={t("sample.copyBarcode")}
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(row.original.barcode);
                showToast("success", t("sample.barcodeCopied"));
              } catch {
                showToast("error", t("sample.copyFailed"));
              }
            }}
          >
            <Copy className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title={t("sample.transition")}
            onClick={() => setSelected(row.original)}
            disabled={(STATUS_TRANSITIONS[row.original.status] || []).length === 0}
          >
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("sample.title")} description={t("sample.subtitle")} />

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
            data={samples}
            loading={isLoading}
            error={isError ? (error as Error) : null}
            onRetry={() => refetch()}
            toolbar={
              <div className="flex w-full flex-wrap items-center justify-between gap-3">
                <div className="relative">
                  <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input placeholder={t("sample.search")} value={search} onChange={(e) => setSearch(e.target.value)} className="ps-9 w-80" />
                </div>
                <Button onClick={() => setCreateOpen(true)}>
                  <Plus className="h-4 w-4" />
                  {t("sample.register")}
                </Button>
              </div>
            }
          />
        </CardContent>
      </Card>

      <RegisterSampleDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          queryClient.invalidateQueries({ queryKey: ["samples"] });
          showToast("success", t("sample.registered"));
        }}
      />

      <TransitionDialog
        sample={selected}
        onClose={() => setSelected(null)}
        onTransition={(status, reason) => {
          if (selected) statusMutation.mutate({ barcode: selected.barcode, status, rejection_reason: reason });
        }}
        loading={statusMutation.isPending}
      />
    </div>
  );
}

function RegisterSampleDialog({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: () => void }) {
  const { t } = useTranslation();
  const [orderId, setOrderId] = useState("");
  const [sampleType, setSampleType] = useState("");
  const [collectedBy, setCollectedBy] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { data: orders } = useQuery({
    queryKey: ["orders-for-samples"],
    queryFn: () => ordersApi.list({ limit: 50 }),
    enabled: open,
  });

  useEffect(() => {
    if (!open) return;
    setOrderId("");
    setSampleType("");
    setCollectedBy("");
    setNotes("");
    setError("");
  }, [open]);

  const handleSubmit = async () => {
    setError("");
    if (!orderId) {
      setError(t("sample.selectOrder"));
      return;
    }
    if (!sampleType) {
      setError(t("sample.selectType"));
      return;
    }
    setLoading(true);
    try {
      await samplesApi.create({
        order_id: Number(orderId),
        sample_type: sampleType,
        collected_by: collectedBy || undefined,
        notes: notes || undefined,
      });
      onCreated();
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={t("sample.register")}
      description={t("sample.registerDesc")}
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
          <label className="text-sm font-medium">{t("sample.order")} *</label>
          <Select
            options={(orders || []).map((o) => ({
              value: String(o.id),
              label: `${o.patient_name || `#${o.id}`} — ${o.status}`,
            }))}
            placeholder={t("sample.selectOrder")}
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("sample.sampleType")} *</label>
          <Select
            options={SAMPLE_TYPES.map((type) => ({ value: type, label: t(`sample.${type}`) }))}
            placeholder={t("sample.selectType")}
            value={sampleType}
            onChange={(e) => setSampleType(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("sample.collectedBy")}</label>
          <Input value={collectedBy} onChange={(e) => setCollectedBy(e.target.value)} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("sample.notes")}</label>
          <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>
      </div>
    </Dialog>
  );
}

function TransitionDialog({
  sample,
  onClose,
  onTransition,
  loading,
}: {
  sample: Sample | null;
  onClose: () => void;
  onTransition: (status: string, reason?: string) => void;
  loading: boolean;
}) {
  const { t } = useTranslation();
  const [status, setStatus] = useState("");
  const [reason, setReason] = useState("");

  useEffect(() => {
    if (!sample) return;
    setStatus("");
    setReason("");
  }, [sample]);

  const allowed = sample ? STATUS_TRANSITIONS[sample.status] || [] : [];

  return (
    <Dialog
      open={!!sample}
      onClose={onClose}
      title={t("sample.transition")}
      description={sample ? `${sample.barcode} — ${sample.sample_type}` : undefined}
      footer={
        <>
          <Button variant="outline" onClick={onClose}>{t("common.cancel")}</Button>
          <Button
            onClick={() => onTransition(status, reason || undefined)}
            disabled={!status}
            loading={loading}
          >
            {t("common.confirm")}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("sample.status")} *</label>
          <Select
            options={allowed.map((s) => ({ value: s, label: t(`sample.${s}`) }))}
            placeholder={t("common.select")}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          />
        </div>
        {status === "rejected" && (
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("sample.rejectionReason")} *</label>
            <Textarea value={reason} onChange={(e) => setReason(e.target.value)} />
          </div>
        )}
      </div>
    </Dialog>
  );
}
