from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.health_data.warehouse.service import WarehouseQuery, WarehouseService

logger = logging.getLogger("gula.research_platform.gis")


@dataclass
class GeoLocation:
    latitude: float
    longitude: float
    elevation_m: float | None = None
    accuracy_m: float | None = None


@dataclass
class HealthFacility:
    facility_id: str
    name: str
    facility_type: str = ""
    location: GeoLocation | None = None
    address: str = ""
    city: str = ""
    governorate: str = ""
    capacity: int = 0
    services: list[str] = field(default_factory=list)
    is_active: bool = True


class GISService:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()
        self._facilities: dict[str, HealthFacility] = {}
        self._boundaries: dict[str, list[GeoLocation]] = {}

    def register_facility(self, facility: HealthFacility) -> None:
        self._facilities[facility.facility_id] = facility
        logger.info("GIS facility registered: %s (%s)", facility.facility_id, facility.name)

    def get_facility(self, facility_id: str) -> HealthFacility | None:
        return self._facilities.get(facility_id)

    def list_facilities(
        self,
        governorate: str | None = None,
        facility_type: str | None = None,
    ) -> list[HealthFacility]:
        results = list(self._facilities.values())
        if governorate:
            results = [f for f in results if f.governorate == governorate]
        if facility_type:
            results = [f for f in results if f.facility_type == facility_type]
        return results

    def search_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: float = 10.0,
        facility_type: str | None = None,
    ) -> list[dict[str, Any]]:
        nearby = []
        for fid, fac in self._facilities.items():
            if not fac.location:
                continue
            dist = self._haversine(lat, lon, fac.location.latitude, fac.location.longitude)
            if dist <= radius_km:
                if facility_type and fac.facility_type != facility_type:
                    continue
                nearby.append({
                    "facility_id": fid,
                    "name": fac.name,
                    "type": fac.facility_type,
                    "distance_km": round(dist, 2),
                    "location": {"lat": fac.location.latitude, "lon": fac.location.longitude},
                })
        return sorted(nearby, key=lambda x: x["distance_km"])

    def set_boundary(self, region: str, boundary: list[GeoLocation]) -> None:
        self._boundaries[region] = boundary
        logger.info("GIS boundary set for region: %s (%d points)", region, len(boundary))

    def get_boundary(self, region: str) -> list[GeoLocation] | None:
        return self._boundaries.get(region)

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        import math
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c


class HeatMapGenerator:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def generate(
        self,
        metric: str,
        region: str = "",
        date_from: str = "",
        date_to: str = "",
        granularity: str = "governorate",
    ) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["governorate"],
            measures=["diagnosis_count"],
            group_by=["governorate"],
        )
        if region:
            query.filters["governorate"] = region
        result = self._warehouse.query(query)
        return {
            "metric": metric,
            "region": region,
            "granularity": granularity,
            "type": "choropleth",
            "data_points": result.get("rows", []),
            "note": "Requires geographic boundary data for full rendering",
        }

    def density_map(
        self,
        disease: str,
        region: str = "",
    ) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["governorate"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["governorate"],
        )
        if region:
            query.filters["governorate"] = region
        result = self._warehouse.query(query)
        return {
            "disease": disease,
            "region": region,
            "type": "density",
            "data_points": result.get("rows", []),
        }


class FacilityMapper:
    def __init__(self, gis: GISService | None = None):
        self._gis = gis or GISService()

    def facility_distribution(self, governorate: str | None = None) -> dict[str, Any]:
        facilities = self._gis.list_facilities(governorate=governorate)
        by_type: dict[str, int] = {}
        for f in facilities:
            by_type[f.facility_type] = by_type.get(f.facility_type, 0) + 1
        return {
            "governorate": governorate,
            "total_facilities": len(facilities),
            "by_type": by_type,
            "facilities": [
                {
                    "id": f.facility_id,
                    "name": f.name,
                    "type": f.facility_type,
                    "city": f.city,
                    "location": {"lat": f.location.latitude, "lon": f.location.longitude} if f.location else None,
                }
                for f in facilities
            ],
        }

    def coverage_analysis(self, governorate: str) -> dict[str, Any]:
        facilities = self._gis.list_facilities(governorate=governorate)
        population = 0
        facilities_with_location = [f for f in facilities if f.location]
        return {
            "governorate": governorate,
            "total_facilities": len(facilities),
            "facilities_with_coordinates": len(facilities_with_location),
            "population_served": population,
            "facilities_per_population": None,
        }


class ResourceDistribution:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def by_region(self, resource_type: str, governorate: str | None = None) -> dict[str, Any]:
        return {
            "resource_type": resource_type,
            "governorate": governorate,
            "distribution": [],
            "note": "Requires resource inventory data integration",
        }

    def gap_analysis(self, resource_type: str) -> dict[str, Any]:
        return {
            "resource_type": resource_type,
            "gaps": [],
            "note": "Requires resource demand vs supply data",
        }


class HotspotDetector:
    def __init__(self, warehouse: WarehouseService | None = None):
        self._warehouse = warehouse or WarehouseService()

    def detect(
        self,
        disease: str,
        min_cases: int = 10,
    ) -> dict[str, Any]:
        query = WarehouseQuery(
            dimensions=["governorate"],
            measures=["diagnosis_count"],
            filters={"encounter_type": disease},
            group_by=["governorate"],
        )
        result = self._warehouse.query(query)
        rows = result.get("rows", [])
        hotspots = [
            r for r in rows
            if (r.get("diagnosis_count") or 0) >= min_cases
        ]
        return {
            "disease": disease,
            "min_cases": min_cases,
            "hotspots": hotspots,
            "total_hotspots": len(hotspots),
        }

    def temporal_hotspots(
        self,
        disease: str,
        time_window: str = "weekly",
    ) -> dict[str, Any]:
        return {
            "disease": disease,
            "time_window": time_window,
            "hotspots": [],
            "note": "Requires temporal scan statistics",
        }


class EnvironmentalCorrelator:
    def __init__(self):
        self._environmental_data: dict[str, dict] = {}

    def load_data(self, region: str, data: dict[str, Any]) -> None:
        self._environmental_data[region] = data
        logger.info("Environmental data loaded for region: %s", region)

    def correlate(
        self,
        disease: str,
        environmental_factor: str,
        region: str = "",
    ) -> dict[str, Any]:
        return {
            "disease": disease,
            "factor": environmental_factor,
            "region": region,
            "correlation": None,
            "note": "Requires both disease incidence and environmental time-series data",
        }

    def air_quality_impact(self, disease: str, region: str = "") -> dict[str, Any]:
        return {
            "disease": disease,
            "region": region,
            "analysis": "pending",
            "note": "Requires air quality monitoring integration",
        }

    def climate_sensitivity(self, disease: str) -> dict[str, Any]:
        return {
            "disease": disease,
            "climate_factors": ["temperature", "precipitation", "humidity"],
            "sensitivity": None,
            "note": "Requires climate data integration and statistical modeling",
        }
