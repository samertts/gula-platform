from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app._compat import UTC

from .models import (
    AIRecommendation,
    CapacityIntelligence,
    IncidentIntelligence,
    NationalKPI,
    SituationRoom,
    SituationRoomStatus,
)


class CommandIntelligenceEngine:
    async def get_situation_status(
        self, db: Session, region: str | None = None,
    ) -> dict[str, Any]:
        query = db.query(SituationRoom)
        if region:
            query = query.filter(SituationRoom.region == region)
        rooms = query.all()

        if not rooms:
            return {
                "overall_status": SituationRoomStatus.GREEN.value,
                "rooms": [],
                "active_alerts": 0,
                "region": region,
            }

        status_scores = {
            SituationRoomStatus.GREEN.value: 0,
            SituationRoomStatus.YELLOW.value: 1,
            SituationRoomStatus.ORANGE.value: 2,
            SituationRoomStatus.RED.value: 3,
        }

        max_score = 0
        total_alerts = 0
        room_list = []

        for room in rooms:
            status = room.status or SituationRoomStatus.GREEN.value
            score = status_scores.get(status, 0)
            max_score = max(max_score, score)
            alerts = room.alerts or []
            total_alerts += len(alerts)
            room_list.append(
                {
                    "id": room.id,
                    "name": room.name,
                    "status": status,
                    "metrics": room.metrics or {},
                    "alerts_count": len(alerts),
                    "region": room.region,
                },
            )

        status_by_score = [
            SituationRoomStatus.GREEN.value,
            SituationRoomStatus.YELLOW.value,
            SituationRoomStatus.ORANGE.value,
            SituationRoomStatus.RED.value,
        ]
        overall_status = status_by_score[max_score]

        return {
            "overall_status": overall_status,
            "rooms": room_list,
            "active_alerts": total_alerts,
            "region": region,
        }

    async def get_national_kpis(
        self, db: Session, category: str | None = None,
    ) -> list[dict[str, Any]]:
        query = db.query(NationalKPI)
        if category:
            query = query.filter(NationalKPI.kpi_category == category)
        kpis = query.order_by(desc(NationalKPI.measured_at)).all()

        return [
            {
                "id": kpi.id,
                "kpi_name": kpi.kpi_name,
                "kpi_category": kpi.kpi_category,
                "kpi_value": kpi.kpi_value,
                "target_value": kpi.target_value,
                "unit": kpi.unit,
                "region": kpi.region,
                "lab_id": kpi.lab_id,
                "measured_at": kpi.measured_at.isoformat() if kpi.measured_at else None,
                "achievement_pct": (
                    round((kpi.kpi_value / kpi.target_value) * 100, 2)
                    if kpi.target_value and kpi.target_value != 0
                    else None
                ),
            }
            for kpi in kpis
        ]

    async def get_active_incidents(
        self, db: Session, severity: str | None = None,
    ) -> list[dict[str, Any]]:
        query = db.query(IncidentIntelligence).filter(
            IncidentIntelligence.status != "resolved",
        )
        if severity:
            query = query.filter(IncidentIntelligence.severity == severity)
        incidents = query.order_by(desc(IncidentIntelligence.detected_at)).all()

        return [
            {
                "id": inc.id,
                "incident_type": inc.incident_type,
                "severity": inc.severity,
                "title": inc.title,
                "description": inc.description,
                "affected_entities": inc.affected_entities,
                "root_cause": inc.root_cause,
                "impact_analysis": inc.impact_analysis,
                "recommendation": inc.recommendation,
                "status": inc.status,
                "detected_at": inc.detected_at.isoformat() if inc.detected_at else None,
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            }
            for inc in incidents
        ]

    async def get_capacity_intelligence(
        self, db: Session, entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        query = db.query(CapacityIntelligence)
        if entity_type:
            query = query.filter(CapacityIntelligence.entity_type == entity_type)
        capacities = query.order_by(desc(CapacityIntelligence.generated_at)).all()

        return [
            {
                "id": cap.id,
                "entity_type": cap.entity_type,
                "entity_id": cap.entity_id,
                "metric": cap.metric,
                "current_value": cap.current_value,
                "threshold": cap.threshold,
                "trend": cap.trend,
                "forecast": cap.forecast,
                "recommendation": cap.recommendation,
                "generated_at": cap.generated_at.isoformat() if cap.generated_at else None,
                "utilization_pct": (
                    round((cap.current_value / cap.threshold) * 100, 2)
                    if cap.threshold and cap.threshold != 0
                    else None
                ),
            }
            for cap in capacities
        ]

    async def generate_recommendation(
        self, db: Session, context: dict[str, Any],
    ) -> dict[str, Any]:
        rec_type = context.get("recommendation_type", "general")
        priority = context.get("priority", 0)
        title = context.get("title", "AI-Generated Recommendation")
        description = context.get("description", "")
        expected_impact = context.get("expected_impact", {})
        risk_assessment = context.get("risk_assessment", {})
        created_by = context.get("created_by")

        recommendation = AIRecommendation(
            recommendation_type=rec_type,
            priority=priority,
            title=title,
            description=description,
            expected_impact=expected_impact,
            risk_assessment=risk_assessment,
            status="pending",
            created_by=created_by,
        )
        db.add(recommendation)
        db.commit()
        db.refresh(recommendation)

        return {
            "id": recommendation.id,
            "recommendation_type": recommendation.recommendation_type,
            "priority": recommendation.priority,
            "title": recommendation.title,
            "description": recommendation.description,
            "expected_impact": recommendation.expected_impact,
            "risk_assessment": recommendation.risk_assessment,
            "status": recommendation.status,
            "created_at": recommendation.created_at.isoformat() if recommendation.created_at else None,
        }

    async def get_live_situation_room(
        self, db: Session, region: str | None = None,
    ) -> dict[str, Any]:
        status = await self.get_situation_status(db, region)
        kpis = await self.get_national_kpis(db)
        incidents = await self.get_active_incidents(db)
        capacity = await self.get_capacity_intelligence(db)

        recommendations = (
            db.query(AIRecommendation)
            .filter(AIRecommendation.status == "pending")
            .order_by(desc(AIRecommendation.priority), desc(AIRecommendation.created_at))
            .limit(10)
            .all()
        )

        return {
            "situation_status": status,
            "kpis": kpis,
            "active_incidents": incidents,
            "capacity": capacity,
            "pending_recommendations": [
                {
                    "id": r.id,
                    "type": r.recommendation_type,
                    "priority": r.priority,
                    "title": r.title,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in recommendations
            ],
            "region": region,
            "refreshed_at": datetime.now(UTC).isoformat(),
        }


class SituationAnalyzer:
    async def analyze_national_health(self, db: Session) -> dict[str, Any]:
        total_kpis = db.query(func.count(NationalKPI.id)).scalar() or 0
        kpis_meeting_target = (
            db.query(func.count(NationalKPI.id))
            .filter(
                NationalKPI.target_value.isnot(None),
                NationalKPI.kpi_value >= NationalKPI.target_value,
            )
            .scalar()
            or 0
        )

        active_incidents = (
            db.query(func.count(IncidentIntelligence.id))
            .filter(IncidentIntelligence.status != "resolved")
            .scalar()
            or 0
        )

        critical_incidents = (
            db.query(func.count(IncidentIntelligence.id))
            .filter(
                IncidentIntelligence.status != "resolved",
                IncidentIntelligence.severity.in_(["critical", "high"]),
            )
            .scalar()
            or 0
        )

        health_score = 0.0
        if total_kpis > 0:
            health_score = round((kpis_meeting_target / total_kpis) * 100, 2)

        if critical_incidents > 0:
            health_score = max(0, health_score - (critical_incidents * 10))

        if health_score >= 80:
            grade = SituationRoomStatus.GREEN.value
        elif health_score >= 60:
            grade = SituationRoomStatus.YELLOW.value
        elif health_score >= 40:
            grade = SituationRoomStatus.ORANGE.value
        else:
            grade = SituationRoomStatus.RED.value

        return {
            "health_score": health_score,
            "grade": grade,
            "total_kpis": total_kpis,
            "kpis_meeting_target": kpis_meeting_target,
            "active_incidents": active_incidents,
            "critical_incidents": critical_incidents,
            "analyzed_at": datetime.now(UTC).isoformat(),
        }

    async def analyze_regional_health(
        self, db: Session, region: str,
    ) -> dict[str, Any]:
        total_kpis = (
            db.query(func.count(NationalKPI.id))
            .filter(NationalKPI.region == region)
            .scalar()
            or 0
        )
        kpis_meeting_target = (
            db.query(func.count(NationalKPI.id))
            .filter(
                NationalKPI.region == region,
                NationalKPI.target_value.isnot(None),
                NationalKPI.kpi_value >= NationalKPI.target_value,
            )
            .scalar()
            or 0
        )

        active_incidents = (
            db.query(func.count(IncidentIntelligence.id))
            .filter(
                IncidentIntelligence.status != "resolved",
                IncidentIntelligence.title.ilike(f"%{region}%"),
            )
            .scalar()
            or 0
        )

        health_score = 0.0
        if total_kpis > 0:
            health_score = round((kpis_meeting_target / total_kpis) * 100, 2)

        if health_score >= 80:
            grade = SituationRoomStatus.GREEN.value
        elif health_score >= 60:
            grade = SituationRoomStatus.YELLOW.value
        elif health_score >= 40:
            grade = SituationRoomStatus.ORANGE.value
        else:
            grade = SituationRoomStatus.RED.value

        return {
            "region": region,
            "health_score": health_score,
            "grade": grade,
            "total_kpis": total_kpis,
            "kpis_meeting_target": kpis_meeting_target,
            "active_incidents": active_incidents,
            "analyzed_at": datetime.now(UTC).isoformat(),
        }

    async def detect_anomalies(self, db: Session) -> list[dict[str, Any]]:
        anomalies = []

        underperforming_kpis = (
            db.query(NationalKPI)
            .filter(
                NationalKPI.target_value.isnot(None),
                NationalKPI.kpi_value < NationalKPI.target_value * 0.5,
            )
            .all()
        )
        for kpi in underperforming_kpis:
            anomalies.append(
                {
                    "type": "kpi_underperformance",
                    "severity": "high",
                    "entity": kpi.kpi_name,
                    "category": kpi.kpi_category,
                    "current_value": kpi.kpi_value,
                    "target_value": kpi.target_value,
                    "region": kpi.region,
                    "details": f"KPI {kpi.kpi_name} at {kpi.kpi_value} is below 50% of target {kpi.target_value}",
                    "detected_at": datetime.now(UTC).isoformat(),
                },
            )

        over_capacity = (
            db.query(CapacityIntelligence)
            .filter(
                CapacityIntelligence.threshold.isnot(None),
                CapacityIntelligence.current_value > CapacityIntelligence.threshold,
            )
            .all()
        )
        for cap in over_capacity:
            anomalies.append(
                {
                    "type": "capacity_exceeded",
                    "severity": "medium",
                    "entity": f"{cap.entity_type}:{cap.entity_id}",
                    "metric": cap.metric,
                    "current_value": cap.current_value,
                    "threshold": cap.threshold,
                    "details": f"Capacity {cap.metric} for {cap.entity_type} {cap.entity_id} exceeds threshold",
                    "detected_at": datetime.now(UTC).isoformat(),
                },
            )

        critical_incidents = (
            db.query(IncidentIntelligence)
            .filter(
                IncidentIntelligence.status != "resolved",
                IncidentIntelligence.severity == "critical",
            )
            .all()
        )
        for inc in critical_incidents:
            anomalies.append(
                {
                    "type": "critical_incident",
                    "severity": "critical",
                    "entity": inc.title,
                    "incident_type": inc.incident_type,
                    "details": inc.description or "Critical active incident",
                    "detected_at": inc.detected_at.isoformat() if inc.detected_at else None,
                },
            )

        return anomalies

    async def compute_national_readiness(self, db: Session) -> dict[str, Any]:
        health = await self.analyze_national_health(db)
        anomalies = await self.detect_anomalies(db)

        capacity_ok = (
            db.query(func.count(CapacityIntelligence.id))
            .filter(
                CapacityIntelligence.threshold.isnot(None),
                CapacityIntelligence.current_value > CapacityIntelligence.threshold * 0.85,
            )
            .scalar()
            or 0
        )
        total_capacity = (
            db.query(func.count(CapacityIntelligence.id))
            .filter(CapacityIntelligence.threshold.isnot(None))
            .scalar()
            or 1
        )

        capacity_readiness = round((1 - capacity_ok / total_capacity) * 100, 2)

        readiness_score = round((health["health_score"] * 0.6 + capacity_readiness * 0.4), 2)

        if readiness_score >= 80:
            readiness_level = "high"
        elif readiness_score >= 60:
            readiness_level = "medium"
        elif readiness_score >= 40:
            readiness_level = "low"
        else:
            readiness_level = "critical"

        return {
            "readiness_score": readiness_score,
            "readiness_level": readiness_level,
            "health_component": health["health_score"],
            "capacity_component": capacity_readiness,
            "active_anomalies": len(anomalies),
            "critical_anomalies": sum(1 for a in anomalies if a["severity"] == "critical"),
            "assessed_at": datetime.now(UTC).isoformat(),
        }


class KPIEngine:
    async def calculate_kpi(
        self, db: Session, kpi_name: str, region: str | None = None,
    ) -> float | None:
        query = db.query(NationalKPI).filter(NationalKPI.kpi_name == kpi_name)
        if region:
            query = query.filter(NationalKPI.region == region)
        latest = query.order_by(desc(NationalKPI.measured_at)).first()

        if latest is None:
            return None
        return latest.kpi_value

    async def get_kpi_trend(
        self, db: Session, kpi_name: str, days: int = 30,
    ) -> list[dict[str, Any]]:
        since = datetime.now(UTC) - timedelta(days=days)
        kpis = (
            db.query(NationalKPI)
            .filter(
                NationalKPI.kpi_name == kpi_name,
                NationalKPI.measured_at >= since,
            )
            .order_by(NationalKPI.measured_at)
            .all()
        )

        return [
            {
                "kpi_name": kpi.kpi_name,
                "kpi_value": kpi.kpi_value,
                "target_value": kpi.target_value,
                "unit": kpi.unit,
                "region": kpi.region,
                "measured_at": kpi.measured_at.isoformat() if kpi.measured_at else None,
            }
            for kpi in kpis
        ]

    async def compare_kpis(
        self, db: Session, region_a: str, region_b: str,
    ) -> dict[str, Any]:
        categories = (
            db.query(NationalKPI.kpi_category)
            .distinct()
            .filter(
                NationalKPI.region.in_([region_a, region_b]),
            )
            .all()
        )
        category_names = [c[0] for c in categories]

        comparisons = []
        for category in category_names:
            a_avg = (
                db.query(func.avg(NationalKPI.kpi_value))
                .filter(
                    NationalKPI.region == region_a,
                    NationalKPI.kpi_category == category,
                )
                .scalar()
                or 0
            )
            b_avg = (
                db.query(func.avg(NationalKPI.kpi_value))
                .filter(
                    NationalKPI.region == region_b,
                    NationalKPI.kpi_category == category,
                )
                .scalar()
                or 0
            )
            comparisons.append(
                {
                    "category": category,
                    "region_a": {"region": region_a, "average_value": round(float(a_avg), 2)},
                    "region_b": {"region": region_b, "average_value": round(float(b_avg), 2)},
                    "difference": round(float(a_avg - b_avg), 2),
                },
            )

        return {
            "region_a": region_a,
            "region_b": region_b,
            "comparisons": comparisons,
            "compared_at": datetime.now(UTC).isoformat(),
        }


engine = CommandIntelligenceEngine()
analyzer = SituationAnalyzer()
kpi_engine = KPIEngine()
