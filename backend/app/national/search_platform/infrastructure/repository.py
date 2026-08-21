from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.national.search_platform.domain.entities import SavedSearch, SearchResult
from app.national.search_platform.domain.repository import (
    SavedSearchRepository,
    SearchResultRepository,
)
from app.national.search_platform.infrastructure.models import (
    NationalSavedSearch,
    NationalSearchResult,
)


class SQLAlchemySavedSearchRepository(SavedSearchRepository):

    def __init__(self, db: Session, lab_id: int) -> None:
        self.db = db
        self.lab_id = lab_id

    async def save(self, saved: SavedSearch) -> SavedSearch:
        model = self.db.query(NationalSavedSearch).filter(
            NationalSavedSearch.id == saved.id,
            NationalSavedSearch.lab_id == self.lab_id,
        ).first()
        if model:
            model.name = saved.name
            model.description = saved.description
            model.query = saved.query
            model.index_types = [t.value for t in saved.index_types]
            model.created_by = saved.created_by
            model.scheduled = saved.scheduled
            model.schedule_cron = saved.schedule_cron
        else:
            model = NationalSavedSearch(
                id=saved.id,
                lab_id=self.lab_id,
                name=saved.name,
                description=saved.description,
                query=saved.query,
                index_types=[t.value for t in saved.index_types],
                created_by=saved.created_by,
                scheduled=saved.scheduled,
                schedule_cron=saved.schedule_cron,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, search_id: str) -> SavedSearch | None:
        model = self.db.query(NationalSavedSearch).filter(
            NationalSavedSearch.id == search_id,
            NationalSavedSearch.lab_id == self.lab_id,
            ~NationalSavedSearch.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        created_by: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SavedSearch]:
        query = self.db.query(NationalSavedSearch).filter(
            NationalSavedSearch.lab_id == self.lab_id,
            ~NationalSavedSearch.is_deleted,
        )
        if created_by:
            query = query.filter(NationalSavedSearch.created_by == created_by)
        models = query.order_by(NationalSavedSearch.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, search_id: str) -> None:
        model = self.db.query(NationalSavedSearch).filter(
            NationalSavedSearch.id == search_id,
            NationalSavedSearch.lab_id == self.lab_id,
            ~NationalSavedSearch.is_deleted,
        ).first()
        if model:
            model.is_deleted = True
            model.deleted_at = datetime.now(UTC)
            self.db.commit()

    async def find_scheduled(self) -> list[SavedSearch]:
        models = self.db.query(NationalSavedSearch).filter(
            NationalSavedSearch.lab_id == self.lab_id,
            NationalSavedSearch.scheduled,
            ~NationalSavedSearch.is_deleted,
        ).all()
        return [m.to_domain() for m in models]


class SQLAlchemySearchResultRepository(SearchResultRepository):

    def __init__(self, db: Session, lab_id: int) -> None:
        self.db = db
        self.lab_id = lab_id

    async def save_result(self, result: SearchResult) -> SearchResult:
        model = self.db.query(NationalSearchResult).filter(
            NationalSearchResult.id == result.id,
            NationalSearchResult.lab_id == self.lab_id,
        ).first()
        if model:
            model.query_id = result.query_id
            model.index_type = result.index_type.value
            model.resource_id = result.resource_id
            model.resource_type = result.resource_type
            model.score = result.score
            model.title = result.title
            model.description = result.description
            model.highlights = result.highlights
            model.matched_fields = result.matched_fields
            model.metadata_ = result.metadata
            model.url = result.url
        else:
            model = NationalSearchResult(
                id=result.id,
                lab_id=self.lab_id,
                query_id=result.query_id,
                index_type=result.index_type.value,
                resource_id=result.resource_id,
                resource_type=result.resource_type,
                score=result.score,
                title=result.title,
                description=result.description,
                highlights=result.highlights,
                matched_fields=result.matched_fields,
                metadata_=result.metadata,
                url=result.url,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def save_results(self, results: list[SearchResult]) -> list[SearchResult]:
        saved = []
        for r in results:
            saved.append(await self.save_result(r))
        return saved

    async def get_stats(self) -> dict[str, Any]:
        total = self.db.query(func.count(NationalSearchResult.id)).filter(
            NationalSearchResult.lab_id == self.lab_id,
            ~NationalSearchResult.is_deleted,
        ).scalar() or 0
        by_index = self.db.query(
            NationalSearchResult.index_type,
            func.count(NationalSearchResult.id).label("count"),
        ).filter(
            NationalSearchResult.lab_id == self.lab_id,
            ~NationalSearchResult.is_deleted,
        ).group_by(NationalSearchResult.index_type).all()
        return {
            "total_searches": total,
            "by_index_type": {row.index_type: row.count for row in by_index},
        }
