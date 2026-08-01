import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { patientsApi } from "@/api/endpoints";
import { Card, CardContent, Input, Badge, DataTable, Button, Dialog, Select } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Search, Plus, Pencil } from "lucide-react";
import { useEffect, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";
import type { Patient } from "@/types";
import { formatDate, getErrorMessage, getGenderLabel } from "@/lib/utils";
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
