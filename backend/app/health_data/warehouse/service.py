from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

logger = logging.getLogger("gula.health_data.warehouse.service")


@dataclass
class WarehouseQuery:
    dimensions: list[str] = field(default_factory=list)
    measures: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    group_by: list[str] = field(default_factory=list)
    order_by: str = ""
    order_desc: bool = True
    limit: int = 100
    offset: int = 0
    date_from: date | None = None
    date_to: date | None = None
    tenant_id: str = ""


class WarehouseService:
    def __init__(self):
        self._data: dict[str, list[dict]] = {}

    def load_fact(self, fact_table: str, rows: list[dict]) -> None:
        self._data[fact_table] = rows
        logger.info("Warehouse fact loaded: %s (%d rows)", fact_table, len(rows))

    def load_dimension(self, dim_table: str, rows: list[dict]) -> None:
        self._data[dim_table] = rows
        logger.info("Warehouse dimension loaded: %s (%d rows)", dim_table, len(rows))

    def query(self, query: WarehouseQuery) -> dict[str, Any]:
        import time

        start = time.monotonic()

        fact_table = query.dimensions[0].split(".")[0] if query.dimensions else ""
        data = self._data.get(fact_table, [])

        if query.filters:
            filtered = []
            for row in data:
                match = True
                for key, value in query.filters.items():
                    if key not in row or row[key] != value:
                        match = False
                        break
                if match:
                    filtered.append(row)
            data = filtered

        if query.date_from or query.date_to:
            date_filtered = []
            for row in data:
                row_date = row.get("created_at") or row.get("ordered_at") or row.get("performed_at")
                if row_date:
                    if isinstance(row_date, str):
                        try:
                            row_date = datetime.fromisoformat(row_date).date()
                        except (ValueError, TypeError):
                            continue
                    elif isinstance(row_date, datetime):
                        row_date = row_date.date()
                    if query.date_from and row_date < query.date_from:
                        continue
                    if query.date_to and row_date > query.date_to:
                        continue
                date_filtered.append(row)
            data = date_filtered

        if query.group_by:
            groups: dict[str, dict] = {}
            for row in data:
                key = tuple(str(row.get(g, "")) for g in query.group_by)
                if key not in groups:
                    groups[key] = {g: row.get(g) for g in query.group_by}
                    for m in query.measures:
                        groups[key][m] = 0
                for m in query.measures:
                    val = row.get(m, 0)
                    if isinstance(val, (int, float)):
                        groups[key][m] = (groups[key].get(m, 0) or 0) + val
            data = list(groups.values())

        if query.order_by:
            data = sorted(
                data, key=lambda r: r.get(query.order_by, 0) or 0, reverse=query.order_desc
            )

        total = len(data)
        page = data[query.offset : query.offset + query.limit]

        duration = (time.monotonic() - start) * 1000

        return {
            "columns": list(set(query.dimensions + query.measures)),
            "rows": page,
            "total_rows": total,
            "returned_rows": len(page),
            "duration_ms": round(duration, 1),
        }

    def get_dimension(self, dim_name: str) -> list[dict]:
        return self._data.get(dim_name, [])

    def get_fact(self, fact_name: str) -> list[dict]:
        return self._data.get(fact_name, [])

    def clear(self) -> None:
        self._data.clear()
        logger.info("Warehouse data cleared")
