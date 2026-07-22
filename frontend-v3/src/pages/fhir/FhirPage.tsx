import { useState } from "react";
import { PageHeader } from "@/components/shared/PageComponents";
import { FhirExplorerPage } from "./FhirExplorerPage";
import { FhirPatientPage } from "./FhirPatientPage";
import { FhirObservationPage } from "./FhirObservationPage";
import { FhirReportPage } from "./FhirReportPage";
import { Search, User, FlaskConical, FileText } from "lucide-react";

const TABS = [
  { id: "explorer", label: "المستعرض", icon: Search },
  { id: "patient", label: "المريض", icon: User },
  { id: "observation", label: "الملاحظة", icon: FlaskConical },
  { id: "report", label: "التقرير", icon: FileText },
] as const;

type TabId = (typeof TABS)[number]["id"];

export function FhirPage() {
  const [activeTab, setActiveTab] = useState<TabId>("explorer");

  return (
    <div className="space-y-6">
      <PageHeader
        title="FHIR"
        description="استعراض موارد FHIR للتوافق مع المعايير الدولية"
      />

      <div className="flex border-b" role="tablist">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors
                ${
                  isActive
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                }
              `}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div role="tabpanel">
        {activeTab === "explorer" && <FhirExplorerPage />}
        {activeTab === "patient" && <FhirPatientPage />}
        {activeTab === "observation" && <FhirObservationPage />}
        {activeTab === "report" && <FhirReportPage />}
      </div>
    </div>
  );
}
