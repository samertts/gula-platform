import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardTitle, CardHeader, Input, Button, Badge } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { identityApi, patientsApi } from "@/api/endpoints";
import { Shield, Users, Key, Fingerprint, Building2, Scale, FileCheck, Search, Link2 } from "lucide-react";
import { getErrorMessage } from "@/lib/utils";
import type { Patient } from "@/types";

export function IdentityPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const items = [
    { icon: Shield, title: "niam.governance", desc: "niam.governanceDesc", path: "/niam/governance" },
    { icon: Users, title: "niam.federation", desc: "niam.federationDesc", path: "/niam/federation" },
    { icon: Key, title: "niam.lifecycle", desc: "niam.lifecycleDesc", path: "/niam/lifecycle" },
    { icon: Fingerprint, title: "niam.adaptiveAuth", desc: "niam.adaptiveAuthDesc", path: "/niam/adaptive-auth" },
    { icon: Building2, title: "niam.trust", desc: "niam.trustDesc", path: "/niam/trust" },
    { icon: Scale, title: "niam.workflows", desc: "niam.workflowsDesc", path: "/niam/workflows" },
    { icon: FileCheck, title: "niam.certificates", desc: "niam.certificatesDesc", path: "/niam/certificates" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title={t("identity.title")} description={t("identity.subtitle")} />

      <Card>
        <CardHeader><CardTitle>{t("identity.nidLookup")}</CardTitle></CardHeader>
        <CardContent>
          <NidLookupCard />
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.path}
            className="cursor-pointer"
            onClick={() => navigate(item.path)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") navigate(item.path); }}
          >
            <Card className="hover:bg-accent transition-colors">
              <CardContent className="flex items-start gap-4 p-6">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <item.icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-base">{t(item.title)}</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">{t(item.desc)}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
    </div>
  );
}

function NidLookupCard() {
  const { t } = useTranslation();
  const [nationalId, setNationalId] = useState("");
  const [patientSearch, setPatientSearch] = useState("");
  const [patient, setPatient] = useState<Patient | null>(null);
  const [toast, setToast] = useState<{ kind: "success" | "error"; message: string } | null>(null);
  const [lookupResult, setLookupResult] = useState<{ found: boolean; patient?: Patient } | null>(null);

  const showToast = (kind: "success" | "error", message: string) => {
    setToast({ kind, message });
    window.setTimeout(() => setToast(null), 4000);
  };

  const lookupMutation = useMutation({
    mutationFn: (nid: string) => identityApi.lookupByNid(nid),
    onSuccess: (data) => setLookupResult(data),
    onError: (err) => {
      setLookupResult(null);
      showToast("error", getErrorMessage(err));
    },
  });

  const linkMutation = useMutation({
    mutationFn: () =>
      identityApi.linkNid({
        patient_id: patient?.id as number,
        national_id: nationalId,
      }),
    onSuccess: () => {
      showToast("success", t("identity.linked"));
      setPatient(null);
      setPatientSearch("");
      setLookupResult(null);
    },
    onError: (err) => showToast("error", getErrorMessage(err)),
  });

  const searchPatients = async () => {
    if (!patientSearch.trim()) return;
    try {
      const res = await patientsApi.list({ search: patientSearch, limit: 5 });
      const list = (res as { patients?: Patient[] }).patients || [];
      const first = list[0]; if (first) setPatient(first);
      else showToast("error", t("identity.patientNotFound"));
    } catch (err) {
      showToast("error", getErrorMessage(err));
    }
  };

  return (
    <div className="space-y-4">
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

      <div className="flex flex-wrap items-end gap-3">
        <div className="space-y-2 flex-1 min-w-52">
          <label className="text-sm font-medium">{t("identity.nationalId")}</label>
          <Input
            value={nationalId}
            onChange={(e) => setNationalId(e.target.value)}
            placeholder="0123456789012"
            dir="ltr"
          />
        </div>
        <Button onClick={() => lookupMutation.mutate(nationalId)} loading={lookupMutation.isPending}>
          <Search className="h-4 w-4" />
          {t("identity.lookup")}
        </Button>
      </div>

      {lookupResult && (
        <div className="rounded-md border p-4">
          {lookupResult.found && lookupResult.patient ? (
            <div className="space-y-2">
              <p className="text-sm font-medium">{t("identity.nidFound")}</p>
              <div className="grid gap-2 sm:grid-cols-3">
                <Info label={t("patient.fullName")} value={lookupResult.patient.full_name} />
                <Info label={t("patient.phone")} value={lookupResult.patient.phone} />
                <Info label={t("patient.healthId")} value={lookupResult.patient.health_id || "—"} />
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("identity.nidNotFound")}</p>
          )}
        </div>
      )}

      <div className="border-t pt-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-2 flex-1 min-w-52">
            <label className="text-sm font-medium">{t("identity.patientToLink")}</label>
            <Input
              value={patientSearch}
              onChange={(e) => setPatientSearch(e.target.value)}
              placeholder={t("identity.searchPatient")}
            />
          </div>
          <Button variant="outline" onClick={searchPatients}>
            <Search className="h-4 w-4" />
            {t("identity.search")}
          </Button>
        </div>

        {patient && (
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-md border bg-muted/50 px-3 py-2 text-sm">
            <span>
              {patient.full_name} — {patient.health_id || patient.phone}
            </span>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{nationalId || "—"}</Badge>
              <Button
                size="sm"
                onClick={() => linkMutation.mutate()}
                loading={linkMutation.isPending}
                disabled={!nationalId.trim()}
              >
                <Link2 className="h-4 w-4" />
                {t("identity.link")}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="rounded-md border bg-muted/30 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value ?? "—"}</p>
    </div>
  );
}
