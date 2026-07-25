import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardTitle } from "@/components/ui";
import { PageHeader } from "@/components/shared/PageComponents";
import { Shield, Users, Key, Fingerprint, Building2, Scale, FileCheck } from "lucide-react";

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