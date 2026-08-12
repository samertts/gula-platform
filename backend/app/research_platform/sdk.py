from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.health_data.warehouse.service import WarehouseQuery, WarehouseService
from app.research_platform.bi_dashboards import (
    ClinicalDashboard,
    DirectorateDashboard,
    ExecutiveDashboard,
    FinanceDashboard,
    HospitalDashboard,
    LaboratoryDashboard,
    PopulationDashboard,
)
from app.research_platform.data_lake import (
    DataCatalog,
    DataLakeManager,
    DataLineage,
    DataVersioning,
)
from app.research_platform.data_science import (
    EvaluationFramework,
    ExperimentTracker,
    FeatureStore,
    MLPipeline,
    ModelRegistry,
    NotebookManager,
)
from app.research_platform.epidemiology import (
    ClusterDetector,
    EarlyWarningSystem,
    ForecastingEngine,
    OutbreakDetection,
    RealTimeSurveillance,
    RiskModeler,
    TrendAnalyzer,
)
from app.research_platform.gis import GISService, HeatMapGenerator, HotspotDetector
from app.research_platform.kpi_engine import KpiCalculator, KpiDashboard, KPIEngine, KpiRegistry
from app.research_platform.population_health import (
    ChildHealthAnalytics,
    CommunicableDiseaseAnalytics,
    MaternalHealthAnalytics,
    MentalHealthAnalytics,
    NCDAnalytics,
    PopulationAnalytics,
    VaccinationAnalytics,
)
from app.research_platform.privacy import (
    ConsentEnforcement,
    DeIdentificationService,
    DifferentialPrivacy,
    EthicsReviewWorkflow,
    PseudonymizationService,
    ResearchApprovalWorkflow,
)
from app.research_platform.registries import (
    BirthRegistry,
    CancerRegistry,
    CardiovascularRegistry,
    DeathRegistry,
    DiabetesRegistry,
    RareDiseaseRegistry,
    RegistryManager,
)
from app.research_platform.research import (
    DatasetRegistry,
    InstitutionManager,
    PublicationTracker,
    ResearchSandbox,
    StudyManager,
)

logger = logging.getLogger("gula.research_platform.sdk")


class ResearchSDK:
    def __init__(
        self,
        data_lake: DataLakeManager | None = None,
        warehouse: WarehouseService | None = None,
    ):
        self._data_lake = data_lake or DataLakeManager()
        self._warehouse = warehouse or WarehouseService()

        self.studies = StudyManager(self._data_lake)
        self.datasets = DatasetRegistry(self._data_lake.catalog)
        self.institutions = InstitutionManager()
        self.publications = PublicationTracker()
        self.sandbox = ResearchSandbox(self._data_lake)
        self.data_catalog: DataCatalog = self._data_lake.catalog
        self.lineage: DataLineage = self._data_lake.lineage
        self.versioning: DataVersioning = self._data_lake.versioning

        self.population = PopulationAnalytics(self._warehouse)
        self.maternal = MaternalHealthAnalytics(self._warehouse)
        self.child_health = ChildHealthAnalytics(self._warehouse)
        self.ncd = NCDAnalytics(self._warehouse)
        self.communicable = CommunicableDiseaseAnalytics(self._warehouse)
        self.vaccination = VaccinationAnalytics(self._warehouse)
        self.mental_health = MentalHealthAnalytics(self._warehouse)

        self.surveillance = RealTimeSurveillance(self._warehouse)
        self.outbreak = OutbreakDetection(self._warehouse)
        self.clusters = ClusterDetector(self._warehouse)
        self.trends = TrendAnalyzer(self._warehouse)
        self.forecasting = ForecastingEngine(self._warehouse)
        self.risk_modeling = RiskModeler(self._warehouse)
        self.early_warning = EarlyWarningSystem(self.surveillance, self.outbreak)

        self.kpi_registry = KpiRegistry()
        self.kpi_calculator = KpiCalculator(self._warehouse)
        self.kpi_engine = KPIEngine(self.kpi_registry, self.kpi_calculator)
        self.kpi_dashboard = KpiDashboard(self.kpi_engine)

        self.gis = GISService(self._warehouse)
        self.heatmaps = HeatMapGenerator(self._warehouse)
        self.hotspots = HotspotDetector(self._warehouse)

        self.executive_dashboard = ExecutiveDashboard(kpi=self.kpi_engine)
        self.directorate_dashboard = DirectorateDashboard(warehouse=self._warehouse)
        self.hospital_dashboard = HospitalDashboard(self._warehouse)
        self.lab_dashboard = LaboratoryDashboard(self._warehouse)
        self.clinical_dashboard = ClinicalDashboard(self._warehouse)
        self.finance_dashboard = FinanceDashboard()
        self.population_dashboard = PopulationDashboard(self.population, self._warehouse)

        self.registries = RegistryManager(self._warehouse)
        self.cancer_registry = CancerRegistry(self.registries)
        self.birth_registry = BirthRegistry(self.registries)
        self.death_registry = DeathRegistry(self.registries)
        self.diabetes_registry = DiabetesRegistry(self.registries)
        self.cardiovascular_registry = CardiovascularRegistry(self.registries)
        self.rare_disease_registry = RareDiseaseRegistry(self.registries)

        self.notebooks = NotebookManager()
        self.ml_pipelines = MLPipeline()
        self.feature_store = FeatureStore()
        self.experiments = ExperimentTracker()
        self.model_registry = ModelRegistry()
        self.evaluation = EvaluationFramework(self.model_registry)

        self.deid = DeIdentificationService()
        self.pseudonymization = PseudonymizationService()
        self.differential_privacy = DifferentialPrivacy()
        self.consent = ConsentEnforcement()
        self.approvals = ResearchApprovalWorkflow()
        self.ethics = EthicsReviewWorkflow()

    def search_resources(self, query: str) -> dict[str, Any]:
        return {
            "datasets": self.datasets.search(query),
            "institutions": self.institutions.search(query),
            "publications": self.publications.search(query),
            "kpis": self.kpi_registry.search(query),
        }

    def get_platform_status(self) -> dict[str, Any]:
        return {
            "projects": len(self.studies._projects),
            "datasets": len(self.data_catalog.list()),
            "institutions": len(self.institutions.list()),
            "publications": len(self.publications._publications),
            "kpis": len(self.kpi_registry.list()),
            "registries": self.registries.count_by_type(),
            "timestamp": datetime.now(UTC).isoformat(),
        }


class AnalyticsSDK:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def query_warehouse(self, query: WarehouseQuery) -> dict[str, Any]:
        return self._warehouse.query(query)

    def describe_dataset(self, dataset_name: str) -> dict[str, Any]:
        fact = self._warehouse.get_fact(dataset_name)
        dim = self._warehouse.get_dimension(dataset_name)
        data = fact or dim
        return {
            "name": dataset_name,
            "type": "fact" if fact else "dimension" if dim else "unknown",
            "record_count": len(data),
            "columns": list(data[0].keys()) if data else [],
        }

    def list_fact_tables(self) -> list[str]:
        return [
            "hd_wh_fact_encounter",
            "hd_wh_fact_lab_result",
            "hd_wh_fact_order",
        ]

    def list_dimension_tables(self) -> list[str]:
        return [
            "hd_wh_dim_patient",
            "hd_wh_dim_date",
            "hd_wh_dim_facility",
            "hd_wh_dim_provider",
            "hd_wh_dim_lab_test",
        ]


class RegistrySDK:
    def __init__(self, manager: RegistryManager | None = None):
        self._manager = manager or RegistryManager()

    def query(self, registry_type: str, **filters) -> list[dict]:
        from app.research_platform.enums import RegistryType

        try:
            rt = RegistryType(registry_type)
        except ValueError:
            return []
        records = self._manager.query(rt, **filters)
        return [
            {
                "registry_id": r.registry_id,
                "patient_ulid": r.patient_ulid,
                "diagnosis": r.diagnosis,
                "diagnosis_code": r.diagnosis_code,
                "diagnosis_date": r.diagnosis_date.isoformat() if r.diagnosis_date else None,
                "governorate": r.governorate,
                "registered_at": r.registered_at.isoformat(),
            }
            for r in records
        ]

    def count(self, registry_type: str) -> int:
        from app.research_platform.enums import RegistryType

        try:
            rt = RegistryType(registry_type)
        except ValueError:
            return 0
        counts = self._manager.count_by_type()
        return counts.get(rt.value, 0)

    def list_types(self) -> list[str]:
        return [rt.value for rt in self._manager._registries]
