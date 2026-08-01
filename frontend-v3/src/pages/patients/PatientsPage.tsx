import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { patientsApi, canonicalPatientApi, patientHistoryApi, resultsApi, patientCardApi } from "@/api/endpoints";
import { Card, CardContent, Input, Badge, DataTable, Button, Dialog, Select } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Search, Plus, Pencil, QrCode, GitMerge, Download, History } from "lucide-react";
import { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Patient, LabOrder } from "@/types";
import { formatDate, formatDateTime, getErrorMessage, getGenderLabel, downloadBlob } from "@/lib/utils";
import { useDebounce } from "@/hooks/useDebounce";

interface PatientFormState {
  full_name: string;
  phone: string;
  birth_date: string;
  gender: string;
  email: string;
  national_id: string;
  family_id: string;
}

const EMPTY_FORM: PatientFormState = {
  full_name: "",
  phone: "",
  birth_date: "",
  gender: "",
  email: "",
  national_id: "",
  family_id: "",
};

export function PatientsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Patient | null>(null);
  const [mergeOpen, setMergeOpen] = useState(false);
  const [detailPatient, setDetailPatient] = useState<Patient | null>(null);
  const [toast, setToast] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["patients", debouncedSearch],
    queryFn: () => patientsApi.list({ search: debouncedSearch || undefined, limit: 100 }),
  });

  const patients = (data as { patients?: Patient[] } | undefined)?.patients || [];

  const showToast = (kind: "success" | "error", message: string) => {
    setToast({ kind, message });
    window.setTimeout(() => setToast(null), 4000);
  };

  const columns: ColumnDef<Patient>[] = [
    { accessorKey: "full_name", header: t("patient.fullName") },
    { accessorKey: "phone", header: t("patient.phone") },
    { accessorKey: "health_id", header: t("patient.healthId"), cell: ({ row }) => row.original.health_id || "—" },
    {
      accessorKey: "gender",
      header: t("patient.gender"),
      cell: ({ row }) => <Badge variant="secondary">{getGenderLabel(row.original.gender)}</Badge>,
    },
    {
      accessorKey: "date_of_birth",
      header: t("patient.birthDate"),
      cell: ({ row }) => formatDate(row.original.birth_date),
    },
    {
      id: "actions",
      header: t("common.actions"),
      cell: ({ row }) => (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="icon"
            title={t("patient.history")}
            onClick={() => setDetailPatient(row.original)}
          >
            <History className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title={t("patient.qrCard")}
            onClick={async () => {
              try {
                const blob = await patientCardApi.qr(row.original.id);
                downloadBlob(blob, `patient-${row.original.id}-qr.png`);
                showToast("success", t("patient.qrDownloaded"));
              } catch (err) {
                showToast("error", getErrorMessage(err));
              }
            }}
          >
            <QrCode className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            title={t("common.edit")}
            onClick={() => {
              setEditing(row.original);
              setDialogOpen(true);
            }}
          >
            <Pencil className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("patient.title")} description={t("patient.subtitle")} />

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
            data={patients}
            loading={isLoading}
            error={isError ? (error as Error) : null}
            onRetry={() => refetch()}
            toolbar={
              <div className="flex w-full flex-wrap items-center justify-between gap-3">
                <div className="relative">
                  <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder={t("patient.search")}
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="ps-9 w-80"
                  />
                </div>
                <Button
                  onClick={() => {
                    setEditing(null);
                    setDialogOpen(true);
                  }}
                >
                  <Plus className="h-4 w-4" />
                  {t("patient.newPatient")}
                </Button>
                <Button variant="outline" onClick={() => setMergeOpen(true)} title={t("patient.mergePatients")}>
                  <GitMerge className="h-4 w-4" />
                  {t("patient.mergePatients")}
                </Button>
              </div>
            }
          />
        </CardContent>
      </Card>

      <PatientDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        editing={editing}
        onSaved={(message) => {
          queryClient.invalidateQueries({ queryKey: ["patients"] });
          showToast("success", message);
        }}
        onError={(message) => showToast("error", message)}
      />

      <MergePatientsDialog
        open={mergeOpen}
        onClose={() => setMergeOpen(false)}
        onMerged={(message) => {
          queryClient.invalidateQueries({ queryKey: ["patients"] });
          showToast("success", message);
        }}
        onError={(message) => showToast("error", message)}
      />

      <PatientDetailDrawer
        patient={detailPatient}
        onClose={() => setDetailPatient(null)}
        onError={(message) => showToast("error", message)}
      />
    </div>
  );
}

function PatientDialog({
  open,
  onClose,
  editing,
  onSaved,
  onError,
}: {
  open: boolean;
  onClose: () => void;
  editing: Patient | null;
  onSaved: (message: string) => void;
  onError: (message: string) => void;
}) {
  const { t } = useTranslation();
  const [form, setForm] = useState<PatientFormState>(EMPTY_FORM);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setError("");
    if (editing) {
      setForm({
        full_name: editing.full_name || "",
        phone: editing.phone || "",
        birth_date: editing.birth_date || "",
        gender: editing.gender || "",
        email: editing.email || "",
        national_id: "",
        family_id: "",
      });
    } else {
      setForm(EMPTY_FORM);
    }
  }, [open, editing]);

  const handleSubmit = async () => {
    setError("");
    if (!form.full_name.trim()) {
      setError(t("validation.required"));
      return;
    }
    if (!form.phone.trim()) {
      setError(t("validation.phone"));
      return;
    }
    setLoading(true);
    try {
      if (editing) {
        await patientsApi.update(editing.id, {
          full_name: form.full_name,
          phone: form.phone,
          birth_date: form.birth_date || undefined,
          gender: form.gender || undefined,
          email: form.email || undefined,
          family_id: form.family_id || undefined,
        });
      } else {
        await patientsApi.create({
          full_name: form.full_name,
          phone: form.phone,
          birth_date: form.birth_date || undefined,
          gender: form.gender || undefined,
          email: form.email || undefined,
          national_id: form.national_id || undefined,
          family_id: form.family_id || undefined,
        });
      }
      onSaved(editing ? t("patient.updated") : t("patient.created"));
      onClose();
    } catch (err) {
      setError(getErrorMessage(err));
      onError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={editing ? t("patient.edit") : t("patient.newPatient")}
      className="max-w-xl"
      footer={
        <>
          <Button variant="outline" onClick={onClose}>{t("common.cancel")}</Button>
          <Button onClick={handleSubmit} loading={loading}>{t("common.save")}</Button>
        </>
      }
    >
      {/* key forces form state reset when dialog target changes */}
      <div key={editing?.id ?? "new"} className="space-y-4">
        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("patient.fullName")} required>
            <Input
              value={form.full_name}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
              placeholder={t("patient.fullName")}
            />
          </Field>
          <Field label={t("patient.phone")} required>
            <Input
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              placeholder="07xxxxxxxxx"
              dir="ltr"
            />
          </Field>
          <Field label={t("patient.birthDate")}>
            <Input
              type="date"
              value={form.birth_date}
              onChange={(e) => setForm((f) => ({ ...f, birth_date: e.target.value }))}
            />
          </Field>
          <Field label={t("patient.gender")}>
            <Select
              options={[
                { value: "male", label: t("patient.male") },
                { value: "female", label: t("patient.female") },
              ]}
              placeholder={t("common.select")}
              value={form.gender}
              onChange={(e) => setForm((f) => ({ ...f, gender: e.target.value }))}
            />
          </Field>
          <Field label={t("patient.email")}>
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              dir="ltr"
            />
          </Field>
          {!editing && (
            <Field label={t("patient.nationalId")}>
              <Input
                value={form.national_id}
                onChange={(e) => setForm((f) => ({ ...f, national_id: e.target.value }))}
                dir="ltr"
              />
            </Field>
          )}
          <Field label={t("patient.familyId")}>
            <Input
              value={form.family_id}
              onChange={(e) => setForm((f) => ({ ...f, family_id: e.target.value }))}
              dir="ltr"
            />
          </Field>
        </div>
      </div>
    </Dialog>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">
        {label}
        {required && <span className="ms-1 text-destructive">*</span>}
      </label>
      {children}
    </div>
  );
}

function MergePatientsDialog({
  open,
  onClose,
  onMerged,
  onError,
}: {
  open: boolean;
  onClose: () => void;
  onMerged: (message: string) => void;
  onError: (message: string) => void;
}) {
  const { t } = useTranslation();
  const [targetSearch, setTargetSearch] = useState("");
  const targetDebounced = useDebounce(targetSearch, 300);
  const [sourceSearch, setSourceSearch] = useState("");
  const sourceDebounced = useDebounce(sourceSearch, 300);
  const [target, setTarget] = useState<Patient | null>(null);
  const [source, setSource] = useState<Patient | null>(null);
  const [error, setError] = useState("");

  const { data: targetResults } = useQuery({
    queryKey: ["patients-search", targetDebounced],
    queryFn: () => patientsApi.list({ search: targetDebounced || undefined, limit: 8 }),
    enabled: open && targetDebounced.length > 0,
  });
  const { data: sourceResults } = useQuery({
    queryKey: ["patients-search", sourceDebounced],
    queryFn: () => patientsApi.list({ search: sourceDebounced || undefined, limit: 8 }),
    enabled: open && sourceDebounced.length > 0,
  });

  const targetPatients = (targetResults as { patients?: Patient[] } | undefined)?.patients || [];
  const sourcePatients = (sourceResults as { patients?: Patient[] } | undefined)?.patients || [];

  const mutation = useMutation({
    mutationFn: () => canonicalPatientApi.merge({ target_id: target!.id, source_id: source!.id }),
    onSuccess: () => {
      setTarget(null);
      setSource(null);
      setTargetSearch("");
      setSourceSearch("");
      onMerged(t("patient.merged"));
      onClose();
    },
    onError: (err) => {
      const msg = getErrorMessage(err);
      setError(msg);
      onError(msg);
    },
  });

  const picker = (
    selected: Patient | null,
    setSelected: (p: Patient | null) => void,
    searchValue: string,
    setSearchValue: (v: string) => void,
    results: Patient[],
    placeholder: string,
  ) => (
    <div className="space-y-2">
      {!selected ? (
        <>
          <Input placeholder={placeholder} value={searchValue} onChange={(e) => setSearchValue(e.target.value)} />
          {results.length > 0 && (
            <div className="max-h-44 overflow-y-auto rounded-md border">
              {results.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className="block w-full px-3 py-2 text-start text-sm hover:bg-accent"
                  onClick={() => setSelected(p)}
                >
                  {p.full_name} — {p.health_id || p.phone || `#${p.id}`}
                </button>
              ))}
            </div>
          )}
        </>
      ) : (
        <div className="flex items-center justify-between rounded-md border bg-muted/50 px-3 py-2 text-sm">
          <span>
            {selected.full_name} — {selected.health_id || selected.phone || `#${selected.id}`}
          </span>
          <Button variant="ghost" size="sm" onClick={() => setSelected(null)}>
            {t("common.clear")}
          </Button>
        </div>
      )}
    </div>
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={t("patient.mergePatients")}
      description={t("patient.mergeHint")}
      className="max-w-lg"
      footer={
        <>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
            disabled={!target || !source || target.id === source.id}
          >
            <GitMerge className="h-4 w-4" />
            {t("patient.mergeConfirm")}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {error && <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
        <div>
          <p className="mb-2 text-sm font-medium">
            {t("patient.mergeTarget")} <span className="text-destructive">*</span>
          </p>
          {picker(target, setTarget, targetSearch, setTargetSearch, targetPatients, t("patient.search"))}
        </div>
        <div>
          <p className="mb-2 text-sm font-medium">
            {t("patient.mergeSource")} <span className="text-destructive">*</span>
          </p>
          {picker(source, setSource, sourceSearch, setSourceSearch, sourcePatients, t("patient.search"))}
        </div>
      </div>
    </Dialog>
  );
}

function PatientDetailDrawer({
  patient,
  onClose,
  onError,
}: {
  patient: Patient | null;
  onClose: () => void;
  onError: (message: string) => void;
}) {
  const { t } = useTranslation();
  const patientId = patient?.id;
  const healthId = patient?.health_id;

  const { data: history, isLoading } = useQuery({
    queryKey: ["patient-history", patientId],
    queryFn: () => patientHistoryApi.byId(patientId as number),
    enabled: !!patientId,
  });

  const { data: timelineData } = useQuery({
    queryKey: ["patient-timeline", healthId],
    queryFn: () => resultsApi.citizenTimeline(healthId as string),
    enabled: !!healthId,
  });

  const { data: children } = useQuery({
    queryKey: ["patient-children", patientId],
    queryFn: () => patientsApi.getChildren(patientId as number),
    enabled: !!patientId,
  });

  const orders = history?.orders || [];
  const results = history?.results || [];
  const timeline = timelineData?.timeline || [];
  const familyMembers = Array.isArray(children) ? children : [];

  return (
    <Dialog
      open={!!patient}
      onClose={onClose}
      title={patient?.full_name}
      description={patient ? `${patient.health_id || ""} — ${formatDate(patient.birth_date)}` : undefined}
      className="max-w-3xl"
      footer={
        <div className="flex items-center gap-2">
          {patient && (
            <>
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    const blob = await patientCardApi.qr(patient.id);
                    downloadBlob(blob, `patient-${patient.id}-qr.png`);
                  } catch (err) {
                    onError(getErrorMessage(err));
                  }
                }}
              >
                <Download className="h-4 w-4" />
                {t("patient.qrDownload")}
              </Button>
              <Button variant="outline" onClick={() => window.open(`/api/patient-card/${patient.id}/print`, "_blank")}>
                {t("patient.cardPrint")}
              </Button>
            </>
          )}
          <Button variant="outline" onClick={onClose}>
            {t("common.close")}
          </Button>
        </div>
      }
    >
      {isLoading ? (
        <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">{t("common.loading")}</div>
      ) : (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border bg-muted/30 p-3">
              <p className="text-xs text-muted-foreground">{t("patient.ordersCount")}</p>
              <p className="text-lg font-semibold">{orders.length}</p>
            </div>
            <div className="rounded-md border bg-muted/30 p-3">
              <p className="text-xs text-muted-foreground">{t("patient.resultsCount")}</p>
              <p className="text-lg font-semibold">{results.length}</p>
            </div>
          </div>

          {timeline.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold">{t("patient.timeline")}</h3>
              <div className="space-y-2">
                {timeline.map((group) => (
                  <div key={group.category} className="rounded-md border p-3">
                    <p className="mb-1 text-sm font-medium text-muted-foreground">{group.category}</p>
                    <div className="space-y-1 text-sm">
                      {group.results.map((r) => (
                        <div key={r.id} className="flex items-center justify-between">
                          <span>
                            {r.test_name}: <strong>{r.value ?? r.value_text ?? "—"}</strong> {r.unit || ""}
                          </span>
                          <span className="text-xs text-muted-foreground">{formatDateTime(r.created_at)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {orders.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold">{t("patient.orders")}</h3>
              <div className="rounded-md border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50 text-muted-foreground">
                      <th className="px-3 py-2 text-start font-medium">{t("order.orderId")}</th>
                      <th className="px-3 py-2 text-start font-medium">{t("order.testsCount")}</th>
                      <th className="px-3 py-2 text-start font-medium">{t("order.status")}</th>
                      <th className="px-3 py-2 text-start font-medium">{t("order.createdAt")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((o: LabOrder) => (
                      <tr key={o.id} className="border-b">
                        <td className="px-3 py-2">#{o.id}</td>
                        <td className="px-3 py-2">{o.results_count ?? o.results?.length ?? "-"}</td>
                        <td className="px-3 py-2">{o.status}</td>
                        <td className="px-3 py-2">{formatDate(o.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {familyMembers.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold">{t("patient.children")}</h3>
              <div className="flex flex-wrap gap-2">
                {familyMembers.map((f: Patient) => (
                  <Badge key={f.id} variant="secondary">
                    {f.full_name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {orders.length === 0 && results.length === 0 && (
            <p className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
              {t("patient.noHistory")}
            </p>
          )}
        </div>
      )}
    </Dialog>
  );
}
