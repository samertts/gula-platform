import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { limsApi, type LimsInstrument } from "@/api/endpoints";
import { Card, CardContent, Badge, DataTable, Button, Dialog, Input, Select, Textarea } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import type { ColumnDef } from "@tanstack/react-table";
import { Plus, Wrench, Thermometer, Wifi, WifiOff, Upload } from "lucide-react";
import { useEffect, useState } from "react";
import { formatDateTime, getErrorMessage } from "@/lib/utils";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  online: "success",
  offline: "secondary",
  maintenance: "warning",
  calibrating: "warning",
  error: "destructive",
};

export function LimsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"instruments" | "import" | "storage">("instruments");
  const [createOpen, setCreateOpen] = useState(false);
  const [maintenance, setMaintenance] = useState<LimsInstrument | null>(null);
  const [calibration, setCalibration] = useState<LimsInstrument | null>(null);
  const [toast, setToast] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const showToast = (kind: "success" | "error", message: string) => {
    setToast({ kind, message });
    window.setTimeout(() => setToast(null), 4000);
  };

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["lims-instruments"] });

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["lims-instruments"],
    queryFn: () => limsApi.instruments(),
  });

  const { data: storage } = useQuery({
    queryKey: ["lims-storage"],
    queryFn: () => limsApi.storage(),
  });

  const instruments = data || [];

  const statusMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: "online" | "offline" }) =>
      action === "online" ? limsApi.instrumentOnline(id) : limsApi.instrumentOffline(id),
    onSuccess: () => {
      refresh();
      showToast("success", t("lims.statusChanged"));
    },
    onError: (err) => showToast("error", getErrorMessage(err)),
  });

  const storageRows = Array.isArray(storage?.storage) ? (storage.storage as Record<string, unknown>[]) : [];

  const columns: ColumnDef<LimsInstrument>[] = [
    { accessorKey: "instrument_code", header: t("lims.code") },
    { accessorKey: "name", header: t("lims.name") },
    {
      accessorKey: "model",
      header: t("lims.model"),
      cell: ({ row }) => row.original.model || "—",
    },
    {
      accessorKey: "status",
      header: t("lims.status"),
      cell: ({ row }) => (
        <Badge variant={statusVariant[row.original.status] || "secondary"}>{row.original.status}</Badge>
      ),
    },
    {
      accessorKey: "location",
      header: t("lims.location"),
      cell: ({ row }) => row.original.location || "—",
    },
    {
      accessorKey: "created_at",
      header: t("lims.createdAt"),
      cell: ({ row }) => (row.original.created_at ? formatDateTime(row.original.created_at) : "—"),
    },
    {
      id: "actions",
      header: t("lims.actions"),
      cell: ({ row }) => {
        const inst = row.original;
        const busy = statusMutation.isPending;
        return (
          <div className="flex flex-wrap gap-2">
            {inst.status === "offline" ? (
              <Button
                size="sm"
                variant="outline"
                loading={busy}
                onClick={() => statusMutation.mutate({ id: inst.id, action: "online" })}
              >
                <Wifi className="h-3.5 w-3.5" />
                {t("lims.bringOnline")}
              </Button>
            ) : (
              <Button
                size="sm"
                variant="outline"
                loading={busy}
                onClick={() => statusMutation.mutate({ id: inst.id, action: "offline" })}
              >
                <WifiOff className="h-3.5 w-3.5" />
                {t("lims.takeOffline")}
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={() => setMaintenance(inst)}>
              <Wrench className="h-3.5 w-3.5" />
              {t("lims.maintenance")}
            </Button>
            <Button size="sm" variant="outline" onClick={() => setCalibration(inst)}>
              <Thermometer className="h-3.5 w-3.5" />
              {t("lims.calibration")}
            </Button>
          </div>
        );
      },
    },
  ];

  const storageColumns: ColumnDef<Record<string, unknown>>[] = [
    { accessorKey: "barcode", header: t("samples.barcode") },
    { accessorKey: "specimen_type", header: t("samples.type") },
    { accessorKey: "rack", header: t("lims.rack"), cell: ({ row }) => row.original.rack || "—" },
    { accessorKey: "shelf", header: t("lims.shelf"), cell: ({ row }) => row.original.shelf || "—" },
    {
      accessorKey: "temperature_c",
      header: t("lims.temperature"),
      cell: ({ row }) => (row.original.temperature_c != null ? `${row.original.temperature_c}°C` : "—"),
    },
    {
      accessorKey: "last_temperature_at",
      header: t("lims.lastTempAt"),
      cell: ({ row }) => (row.original.last_temperature_at ? formatDateTime(String(row.original.last_temperature_at)) : "—"),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("lims.title")} description={t("lims.subtitle")} />

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
            ["instruments", t("lims.instrumentsTab"), Wifi],
            ["import", t("lims.importTab"), Upload],
            ["storage", t("lims.storageTab"), Thermometer],
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

      {tab === "instruments" && (
        <Card>
          <CardContent className="pt-6">
            <DataTable
              columns={columns}
              data={instruments}
              loading={isLoading}
              error={isError ? (error as Error) : null}
              onRetry={() => refetch()}
              toolbar={
                <div className="flex w-full items-center justify-end">
                  <Button onClick={() => setCreateOpen(true)}>
                    <Plus className="h-4 w-4" />
                    {t("lims.newInstrument")}
                  </Button>
                </div>
              }
            />
          </CardContent>
        </Card>
      )}

      {tab === "import" && (
        <AnalyzerImportPanel instruments={instruments} onToast={showToast} />
      )}

      {tab === "storage" && (
        <Card>
          <CardContent className="pt-6">
            <DataTable columns={storageColumns} data={storageRows} loading={isLoading} />
          </CardContent>
        </Card>
      )}

      <CreateInstrumentDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          refresh();
          showToast("success", t("lims.instrumentCreated"));
        }}
        onError={(msg) => showToast("error", msg)}
      />

      {maintenance && (
        <MaintenanceDialog
          instrument={maintenance}
          onClose={() => setMaintenance(null)}
          onDone={() => {
            setMaintenance(null);
            refresh();
            showToast("success", t("lims.maintenanceSaved"));
          }}
          onError={(msg) => showToast("error", msg)}
        />
      )}

      {calibration && (
        <CalibrationDialog
          instrument={calibration}
          onClose={() => setCalibration(null)}
          onDone={() => {
            setCalibration(null);
            refresh();
            showToast("success", t("lims.calibrationSaved"));
          }}
          onError={(msg) => showToast("error", msg)}
        />
      )}
    </div>
  );
}

function CreateInstrumentDialog({
  open,
  onClose,
  onCreated,
  onError,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  onError: (message: string) => void;
}) {
  const { t } = useTranslation();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [model, setModel] = useState("");
  const [location, setLocation] = useState("");

  useEffect(() => {
    if (!open) return;
    setCode("");
    setName("");
    setModel("");
    setLocation("");
  }, [open]);

  const mutation = useMutation({
    mutationFn: () =>
      limsApi.createInstrument({
        instrument_code: code.trim(),
        name: name.trim(),
        model: model.trim() || undefined,
        location: location.trim() || undefined,
      }),
    onSuccess: () => {
      onClose();
      onCreated();
    },
    onError: (err) => onError(getErrorMessage(err)),
  });

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={t("lims.newInstrument")}
      className="max-w-md"
      footer={
        <>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button onClick={() => mutation.mutate()} loading={mutation.isPending} disabled={!code.trim() || !name.trim()}>
            {t("common.create")}
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("lims.code")} *</label>
            <Input value={code} onChange={(e) => setCode(e.target.value)} dir="ltr" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("lims.name")} *</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("lims.model")}</label>
            <Input value={model} onChange={(e) => setModel(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("lims.location")}</label>
            <Input value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>
        </div>
      </div>
    </Dialog>
  );
}

function MaintenanceDialog({
  instrument,
  onClose,
  onDone,
  onError,
}: {
  instrument: LimsInstrument;
  onClose: () => void;
  onDone: () => void;
  onError: (message: string) => void;
}) {
  const { t } = useTranslation();
  const [reason, setReason] = useState("");
  const [nextDue, setNextDue] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      limsApi.instrumentMaintenance(instrument.id, {
        reason: reason.trim() || undefined,
        next_due: nextDue || undefined,
      }),
    onSuccess: () => {
      onClose();
      onDone();
    },
    onError: (err) => onError(getErrorMessage(err)),
  });

  return (
    <Dialog
      open
      onClose={onClose}
      title={`${t("lims.maintenance")} — ${instrument.name}`}
      className="max-w-md"
      footer={
        <>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button onClick={() => mutation.mutate()} loading={mutation.isPending}>
            {t("common.save")}
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("lims.maintenanceReason")}</label>
          <Textarea value={reason} onChange={(e) => setReason(e.target.value)} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("lims.nextDue")}</label>
          <Input type="date" value={nextDue} onChange={(e) => setNextDue(e.target.value)} dir="ltr" />
        </div>
      </div>
    </Dialog>
  );
}

function CalibrationDialog({
  instrument,
  onClose,
  onDone,
  onError,
}: {
  instrument: LimsInstrument;
  onClose: () => void;
  onDone: () => void;
  onError: (message: string) => void;
}) {
  const { t } = useTranslation();
  const [calibrationType, setCalibrationType] = useState("");
  const [result, setResult] = useState("");
  const [nextDue, setNextDue] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      limsApi.instrumentCalibration(instrument.id, {
        calibration_type: calibrationType || undefined,
        result: result.trim() || undefined,
        next_due: nextDue || undefined,
      }),
    onSuccess: () => {
      onClose();
      onDone();
    },
    onError: (err) => onError(getErrorMessage(err)),
  });

  return (
    <Dialog
      open
      onClose={onClose}
      title={`${t("lims.calibration")} — ${instrument.name}`}
      className="max-w-md"
      footer={
        <>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button onClick={() => mutation.mutate()} loading={mutation.isPending}>
            {t("common.save")}
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("lims.calibrationType")}</label>
          <Select
            options={[
              { value: "wavelength", label: "Wavelength" },
              { value: "zero", label: "Zero" },
              { value: "span", label: "Span" },
              { value: "full", label: "Full" },
            ]}
            placeholder={t("common.select")}
            value={calibrationType}
            onChange={(e) => setCalibrationType(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("lims.calibrationResult")}</label>
          <Input value={result} onChange={(e) => setResult(e.target.value)} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">{t("lims.nextDue")}</label>
          <Input type="date" value={nextDue} onChange={(e) => setNextDue(e.target.value)} dir="ltr" />
        </div>
      </div>
    </Dialog>
  );
}

function AnalyzerImportPanel({
  instruments,
  onToast,
}: {
  instruments: LimsInstrument[];
  onToast: (kind: "success" | "error", message: string) => void;
}) {
  const { t } = useTranslation();
  const [protocol, setProtocol] = useState<"astm" | "hl7">("astm");
  const [instrumentId, setInstrumentId] = useState("");
  const [raw, setRaw] = useState("");
  const [lastResult, setLastResult] = useState<{ status: string; results: unknown[] } | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      protocol === "astm"
        ? limsApi.astmReceive({ instrument_id: Number(instrumentId), raw_message: raw })
        : limsApi.hl7Receive({ instrument_id: Number(instrumentId), raw_message: raw }),
    onSuccess: (data) => {
      setLastResult(data);
      onToast("success", t("lims.importDone"));
    },
    onError: (err) => onToast("error", getErrorMessage(err)),
  });

  const valid = instrumentId && raw.trim().length > 0;

  return (
    <Card>
      <CardContent className="space-y-4 pt-6">
        <div className="flex gap-1 rounded-lg border bg-muted/40 p-1">
          {(
            [
              ["astm", "ASTM"],
              ["hl7", "HL7"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setProtocol(key)}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                protocol === key ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">{t("lims.instrument")} *</label>
          <Select
            options={instruments.map((i) => ({ value: String(i.id), label: `${i.instrument_code} — ${i.name}` }))}
            placeholder={t("common.select")}
            value={instrumentId}
            onChange={(e) => setInstrumentId(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">
            {t("lims.rawMessage")} * <span className="text-muted-foreground">({protocol.toUpperCase()})</span>
          </label>
          <Textarea value={raw} onChange={(e) => setRaw(e.target.value)} rows={8} dir="ltr" className="font-mono text-xs" />
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={() => mutation.mutate()} loading={mutation.isPending} disabled={!valid}>
            <Upload className="h-4 w-4" />
            {t("lims.importMessage")}
          </Button>
          <Button variant="ghost" onClick={() => setRaw("")}>
            {t("common.clear")}
          </Button>
        </div>

        {lastResult && (
          <div className="rounded-md border bg-muted/30 p-3 text-sm">
            <p className="font-medium">
              {t("lims.importStatus")}: <span dir="ltr">{lastResult.status}</span>
            </p>
            {Array.isArray(lastResult.results) && lastResult.results.length > 0 && (
              <pre dir="ltr" className="mt-2 max-h-48 overflow-auto rounded bg-background p-2 font-mono text-xs">
                {JSON.stringify(lastResult.results, null, 2)}
              </pre>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
