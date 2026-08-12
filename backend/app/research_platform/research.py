from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.health_data.enums import DataClassification

from .base import ResearchDataset, ResearchInstitution, ResearchProject, ResearchPublication
from .data_lake import DataCatalog, DataLakeManager
from .enums import DatasetCategory, ResearchProjectStatus, StudyType

logger = logging.getLogger("gula.research_platform.research")


@dataclass
class ResearchWorkspace:
    workspace_id: str
    name: str
    description: str = ""
    project_id: str = ""
    members: list[dict] = field(default_factory=list)
    datasets: list[str] = field(default_factory=list)
    notebooks: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_member(self, user_id: str, role: str = "viewer") -> None:
        self.members.append({"user_id": user_id, "role": role, "joined_at": datetime.now(UTC).isoformat()})
        self.updated_at = datetime.now(UTC)

    def remove_member(self, user_id: str) -> bool:
        before = len(self.members)
        self.members = [m for m in self.members if m.get("user_id") != user_id]
        self.updated_at = datetime.now(UTC)
        return len(self.members) < before

    def link_dataset(self, dataset_name: str) -> None:
        if dataset_name not in self.datasets:
            self.datasets.append(dataset_name)
            self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "project_id": self.project_id,
            "members": self.members,
            "datasets": self.datasets,
            "notebooks": self.notebooks,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class StudyManager:
    def __init__(self, data_lake: DataLakeManager | None = None):
        self._projects: dict[str, ResearchProject] = {}
        self._data_lake = data_lake

    def create_project(
        self,
        title: str,
        title_ar: str = "",
        description: str = "",
        study_type: StudyType = StudyType.OBSERVATIONAL,
        principal_investigator: str = "",
        institution_id: str = "",
        data_classification: DataClassification = DataClassification.CONFIDENTIAL,
    ) -> ResearchProject:
        import uuid

        project = ResearchProject(
            id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            title=title,
            title_ar=title_ar,
            description=description,
            study_type=study_type.value,
            status=ResearchProjectStatus.DRAFT.value,
            principal_investigator=principal_investigator,
            institution_id=institution_id,
            data_classification=data_classification.value,
        )
        self._projects[project.id] = project
        logger.info("Research project created: %s (%s)", project.id, title)
        return project

    def get_project(self, project_id: str) -> ResearchProject | None:
        return self._projects.get(project_id)

    def update_status(self, project_id: str, status: ResearchProjectStatus) -> ResearchProject | None:
        project = self._projects.get(project_id)
        if project:
            project.status = status.value
            if status == ResearchProjectStatus.ACTIVE:
                project.start_date = datetime.now(UTC)
            elif status == ResearchProjectStatus.COMPLETED:
                project.end_date = datetime.now(UTC)
            logger.info("Project %s status updated to %s", project_id, status.value)
        return project

    def list_projects(
        self,
        status: ResearchProjectStatus | None = None,
        institution_id: str | None = None,
    ) -> list[ResearchProject]:
        results = list(self._projects.values())
        if status:
            results = [p for p in results if p.status == status.value]
        if institution_id:
            results = [p for p in results if p.institution_id == institution_id]
        return results

    def add_dataset(self, project_id: str, dataset: ResearchDataset) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        sources = project.data_sources or []
        sources.append(dataset.name)
        project.data_sources = sources
        return True

    def add_collaborator(self, project_id: str, collaborator: dict) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        collabs = project.collaborators or []
        collabs.append(collaborator)
        project.collaborators = collabs
        return True


class DatasetRegistry:
    def __init__(self, catalog: DataCatalog | None = None):
        self._catalog = catalog or DataCatalog()

    def register(
        self,
        name: str,
        description: str = "",
        category: DatasetCategory = DatasetCategory.CLINICAL,
        schema: dict[str, str] | None = None,
        classification: DataClassification = DataClassification.CONFIDENTIAL,
        owner: str = "",
        tags: list[str] | None = None,
    ) -> ResearchDataset:
        import uuid

        ds = ResearchDataset(
            id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            name=name,
            description=description,
            category=category.value,
            schema_definition=schema or {},
        )
        self._catalog.register_dataset(
            name=name,
            description=description,
            schema=schema,
            classification=classification,
            owner=owner,
            tags=tags,
        )
        logger.info("Dataset registered: %s (%s)", name, category.value)
        return ds

    def list(self, category: DatasetCategory | None = None) -> list[dict]:
        datasets = self._catalog.list()
        if category:
            datasets = [ds for ds in datasets if category.value in ds.tags]
        return [
            {
                "name": ds.name,
                "description": ds.description,
                "classification": ds.classification.value,
                "quality": ds.quality.value,
                "record_count": ds.record_count,
                "partition_count": len(ds.partitions),
                "tags": ds.tags,
            }
            for ds in datasets
        ]

    def search(self, query: str) -> list[dict]:
        return [
            {
                "name": ds.name,
                "description": ds.description,
                "record_count": ds.record_count,
                "tags": ds.tags,
            }
            for ds in self._catalog.search(query)
        ]


class InstitutionManager:
    def __init__(self):
        self._institutions: dict[str, ResearchInstitution] = {}

    def register(
        self,
        name: str,
        name_ar: str = "",
        institution_type: str = "university",
        city: str = "",
        governorate: str = "",
        contact_email: str = "",
    ) -> ResearchInstitution:
        import uuid

        inst = ResearchInstitution(
            id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            name=name,
            name_ar=name_ar,
            institution_type=institution_type,
            city=city,
            governorate=governorate,
            contact_email=contact_email,
        )
        self._institutions[inst.id] = inst
        logger.info("Institution registered: %s (%s)", inst.id, name)
        return inst

    def get(self, institution_id: str) -> ResearchInstitution | None:
        return self._institutions.get(institution_id)

    def list(self, governorate: str | None = None) -> list[ResearchInstitution]:
        results = list(self._institutions.values())
        if governorate:
            results = [i for i in results if i.governorate == governorate]
        return results

    def search(self, query: str) -> list[ResearchInstitution]:
        q = query.lower()
        return [
            i for i in self._institutions.values()
            if q in i.name.lower() or q in (i.name_ar or "").lower()
        ]


class PublicationTracker:
    def __init__(self):
        self._publications: dict[str, ResearchPublication] = {}

    def register(
        self,
        title: str,
        authors: list[dict],
        journal: str = "",
        doi: str = "",
        pmid: str = "",
        project_id: str = "",
        publication_type: str = "journal_article",
        abstract: str = "",
        keywords: list[str] | None = None,
    ) -> ResearchPublication:
        import uuid

        pub = ResearchPublication(
            id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            title=title,
            authors=authors,
            journal=journal,
            doi=doi,
            pmid=pmid,
            project_id=project_id,
            publication_type=publication_type,
            abstract=abstract,
            keywords=keywords or [],
            publication_date=datetime.now(UTC),
        )
        self._publications[pub.id] = pub
        logger.info("Publication registered: %s (DOI: %s)", pub.id, doi or "N/A")
        return pub

    def get(self, publication_id: str) -> ResearchPublication | None:
        return self._publications.get(publication_id)

    def get_by_doi(self, doi: str) -> ResearchPublication | None:
        for pub in self._publications.values():
            if pub.doi == doi:
                return pub
        return None

    def list_by_project(self, project_id: str) -> list[ResearchPublication]:
        return [p for p in self._publications.values() if p.project_id == project_id]

    def search(self, query: str) -> list[ResearchPublication]:
        q = query.lower()
        return [
            p for p in self._publications.values()
            if q in p.title.lower() or any(q in (kw or "").lower() for kw in (p.keywords or []))
        ]


class ResearchSandbox:
    def __init__(self, data_lake: DataLakeManager | None = None):
        self._data_lake = data_lake
        self._sandboxes: dict[str, dict] = {}

    def create(
        self,
        project_id: str,
        name: str,
        datasets: list[str] | None = None,
        max_records: int = 10000,
        retention_hours: int = 72,
    ) -> dict[str, Any]:
        import uuid

        sandbox_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
        sandbox = {
            "sandbox_id": sandbox_id,
            "project_id": project_id,
            "name": name,
            "datasets": datasets or [],
            "max_records": max_records,
            "retention_hours": retention_hours,
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": datetime.now(UTC).isoformat(),
            "isolated": True,
            "network_restricted": True,
            "audit_enabled": True,
        }
        self._sandboxes[sandbox_id] = sandbox
        logger.info("Research sandbox created: %s", sandbox_id)
        return sandbox

    def get(self, sandbox_id: str) -> dict[str, Any] | None:
        return self._sandboxes.get(sandbox_id)

    def destroy(self, sandbox_id: str) -> bool:
        if sandbox_id in self._sandboxes:
            del self._sandboxes[sandbox_id]
            logger.info("Research sandbox destroyed: %s", sandbox_id)
            return True
        return False

    def list_by_project(self, project_id: str) -> list[dict[str, Any]]:
        return [s for s in self._sandboxes.values() if s.get("project_id") == project_id]
