from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, Float, Index, Integer, String, Text

from app.models.base import TenantMixin
from app.national.base import BaseEntity, _ulid
from app.national.search_platform.domain.enums import SearchIndexType


class NationalSavedSearch(TenantMixin, BaseEntity):
    __tablename__ = "national_search_saved_searches"

    id = Column(String(26), primary_key=True, default=_ulid)
    lab_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True, default="")
    query = Column(JSON, nullable=True, default=dict)
    index_types = Column(JSON, nullable=True, default=list)
    created_by = Column(String(100), nullable=True, index=True)
    scheduled = Column(Boolean, nullable=False, default=False)
    schedule_cron = Column(String(100), nullable=True, default="")

    __table_args__ = (
        Index("ix_nat_search_saved_user", "lab_id", "created_by", "name"),
        Index("ix_nat_search_saved_lab_deleted", "lab_id", "is_deleted"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.search_platform.domain.entities import SavedSearch

        return SavedSearch(
            id=self.id,
            name=self.name,
            description=self.description or "",
            query=self.query or {},
            index_types=[SearchIndexType(t) for t in (self.index_types or [])],
            created_by=self.created_by or "",
            created_at=self.created_at,
            updated_at=self.updated_at,
            scheduled=self.scheduled or False,
            schedule_cron=self.schedule_cron or "",
        )


class NationalSearchResult(TenantMixin, BaseEntity):
    __tablename__ = "national_search_results"

    id = Column(String(26), primary_key=True, default=_ulid)
    lab_id = Column(Integer, nullable=False, index=True)
    query_id = Column(String(26), nullable=False, index=True)
    index_type = Column(String(50), nullable=False)
    resource_id = Column(String(26), nullable=False)
    resource_type = Column(String(100), nullable=True)
    score = Column(Float, nullable=False, default=0.0)
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    highlights = Column(JSON, nullable=True, default=dict)
    matched_fields = Column(JSON, nullable=True, default=list)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    url = Column(String(1000), nullable=True)

    __table_args__ = (
        Index("ix_nat_search_result_query", "lab_id", "query_id", "score"),
        Index("ix_nat_search_result_type_resource", "lab_id", "index_type", "resource_id"),
        Index("ix_nat_search_result_lab_deleted", "lab_id", "is_deleted"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.search_platform.domain.entities import SearchResult

        return SearchResult(
            id=self.id,
            query_id=self.query_id,
            index_type=SearchIndexType(self.index_type),
            resource_id=self.resource_id,
            resource_type=self.resource_type or "",
            score=self.score,
            title=self.title or "",
            description=self.description or "",
            highlights=self.highlights or {},
            matched_fields=self.matched_fields or [],
            metadata=self.metadata_ or {},
            url=self.url or "",
        )
