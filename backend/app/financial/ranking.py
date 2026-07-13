"""Financial Engine — Lab Ranking Service.
Scores and ranks labs for the patient-facing directory.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class LabRanking:
    lab_id: int
    name: str = ""
    quality_score: float = 0.0
    avg_rating: float = 0.0
    review_count: int = 0
    distance_km: Optional[float] = None
    price_level: int = 2  # 1=cheap, 2=medium, 3=expensive
    monthly_volume: int = 0
    response_time_minutes: Optional[int] = None
    accredited: bool = False
    score: float = 0.0
    rank: int = 0


_QUALITY_WEIGHT = 0.30
_RATING_WEIGHT = 0.25
_DISTANCE_WEIGHT = 0.20
_PRICE_WEIGHT = 0.15
_VOLUME_WEIGHT = 0.10

_MAX_DISTANCE_KM = 50.0


def _normalize_distance(distance_km: Optional[float]) -> float:
    if distance_km is None:
        return 0.5  # neutral score
    normalized = 1.0 - min(distance_km, _MAX_DISTANCE_KM) / _MAX_DISTANCE_KM
    return max(0.0, normalized)


def _normalize_price(price_level: int) -> float:
    return {1: 1.0, 2: 0.6, 3: 0.2}.get(price_level, 0.5)


def _normalize_volume(monthly_volume: int) -> float:
    if monthly_volume <= 0:
        return 0.0
    return min(math.log10(monthly_volume) / 3.0, 1.0)


def _normalize_response_time(response_time_minutes: Optional[int]) -> float:
    if response_time_minutes is None:
        return 0.5
    return max(0.0, 1.0 - response_time_minutes / 120.0)


def compute_score(ranking: LabRanking) -> float:
    quality_norm = ranking.quality_score
    rating_norm = ranking.avg_rating / 5.0 if ranking.avg_rating > 0 else 0.0
    distance_norm = _normalize_distance(ranking.distance_km)
    price_norm = _normalize_price(ranking.price_level)
    volume_norm = _normalize_volume(ranking.monthly_volume)

    score = (
        quality_norm * _QUALITY_WEIGHT +
        rating_norm * _RATING_WEIGHT +
        distance_norm * _DISTANCE_WEIGHT +
        price_norm * _PRICE_WEIGHT +
        volume_norm * _VOLUME_WEIGHT
    )
    # Accreditation bonus
    if ranking.accredited:
        score += 0.05

    return round(min(score, 1.0), 4)


def rank_labs(labs: list[LabRanking]) -> list[LabRanking]:
    for lab in labs:
        lab.score = compute_score(lab)

    labs.sort(key=lambda x: x.score, reverse=True)

    for i, lab in enumerate(labs):
        lab.rank = i + 1

    return labs


def anti_dominance_control(labs: list[LabRanking], max_per_owner: int = 3) -> list[LabRanking]:
    owner_counts: dict[str, int] = {}
    filtered: list[LabRanking] = []
    for lab in labs:
        owner_key = str(lab.lab_id // 1000)  # group by owner prefix
        if owner_counts.get(owner_key, 0) < max_per_owner:
            filtered.append(lab)
            owner_counts[owner_key] = owner_counts.get(owner_key, 0) + 1
    return filtered
