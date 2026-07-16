from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.health_data.mdm.matching")


@dataclass
class MatchResult:
    score: float
    method: str
    matched: bool = False
    confidence: float = 0.0
    features: dict[str, Any] = field(default_factory=dict)
    candidate_id: str = ""
    target_id: str = ""


class Matcher(ABC):
    @abstractmethod
    def match(self, source: dict[str, Any], target: dict[str, Any]) -> MatchResult: ...

    @property
    @abstractmethod
    def name(self) -> str: ...


class ExactMatcher(Matcher):
    @property
    def name(self) -> str:
        return "exact"

    def match(self, source: dict[str, Any], target: dict[str, Any]) -> MatchResult:
        fields = ["national_id_hash", "health_number", "license_number", "registration_number"]
        features: dict[str, Any] = {}

        for field in fields:
            src_val = source.get(field)
            tgt_val = target.get(field)
            if src_val and tgt_val and src_val == tgt_val:
                features[field] = True
                return MatchResult(
                    score=1.0,
                    method="exact",
                    matched=True,
                    confidence=1.0,
                    features=features,
                )
            features[field] = False

        name_match = self._name_exact(source, target)
        features["name_exact"] = name_match
        if name_match:
            return MatchResult(
                score=1.0,
                method="exact",
                matched=True,
                confidence=0.95,
                features=features,
                candidate_id=source.get("id", ""),
                target_id=target.get("id", ""),
            )

        return MatchResult(
            score=0.0,
            method="exact",
            matched=False,
            confidence=0.0,
            features=features,
        )

    def _name_exact(self, source: dict, target: dict) -> bool:
        src_first = (source.get("first_name") or "").strip().lower()
        src_last = (source.get("last_name") or "").strip().lower()
        tgt_first = (target.get("first_name") or "").strip().lower()
        tgt_last = (target.get("last_name") or "").strip().lower()
        return src_first == tgt_first and src_last == tgt_last


class FuzzyMatcher(Matcher):
    @property
    def name(self) -> str:
        return "fuzzy"

    def match(self, source: dict[str, Any], target: dict[str, Any]) -> MatchResult:
        score = 0.0
        features: dict[str, Any] = {}
        weights = {"name": 0.35, "dob": 0.25, "phone": 0.20, "email": 0.10, "gender": 0.10}

        name_sim = self._name_similarity(source, target)
        features["name_similarity"] = round(name_sim, 4)
        score += weights["name"] * name_sim

        dob_sim = self._dob_similarity(source, target)
        features["dob_similarity"] = dob_sim
        if dob_sim:
            score += weights["dob"]

        phone_sim = self._exact_field(source, target, "phone")
        features["phone_match"] = phone_sim
        if phone_sim:
            score += weights["phone"]

        email_sim = self._exact_field(source, target, "email")
        features["email_match"] = email_sim
        if email_sim:
            score += weights["email"]

        gender_sim = self._gender_similarity(source, target)
        features["gender_match"] = gender_sim
        if gender_sim:
            score += weights["gender"]

        matched = score >= 0.7
        return MatchResult(
            score=round(score, 4),
            method="fuzzy",
            matched=matched,
            confidence=round(score, 4),
            features=features,
        )

    def _name_similarity(self, source: dict, target: dict) -> float:
        src_full = ((source.get("first_name") or "") + " " + (source.get("last_name") or "")).strip().lower()
        tgt_full = ((target.get("first_name") or "") + " " + (target.get("last_name") or "")).strip().lower()
        if not src_full or not tgt_full:
            return 0.0
        return self._jaro_winkler(src_full, tgt_full)

    def _dob_similarity(self, source: dict, target: dict) -> bool:
        src_dob = source.get("date_of_birth")
        tgt_dob = target.get("date_of_birth")
        if not src_dob or not tgt_dob:
            return False
        return src_dob.strip() == tgt_dob.strip()

    def _gender_similarity(self, source: dict, target: dict) -> bool:
        src_gen = (source.get("gender") or "").strip().lower()
        tgt_gen = (target.get("gender") or "").strip().lower()
        if not src_gen or not tgt_gen:
            return False
        return src_gen[0] == tgt_gen[0]

    def _exact_field(self, source: dict, target: dict, field: str) -> bool:
        src_val = source.get(field)
        tgt_val = target.get(field)
        if not src_val or not tgt_val:
            return False
        return src_val.strip().lower() == tgt_val.strip().lower()

    def _jaro_winkler(self, s1: str, s2: str) -> float:
        if s1 == s2:
            return 1.0
        s1, s2 = s1.lower(), s2.lower()
        len_s1, len_s2 = len(s1), len(s2)
        max_dist = max(len_s1, len_s2) // 2 - 1
        if max_dist < 0:
            max_dist = 0

        s1_matches = [False] * len_s1
        s2_matches = [False] * len_s2
        matches = 0
        transpositions = 0

        for i in range(len_s1):
            start = max(0, i - max_dist)
            end = min(i + max_dist + 1, len_s2)
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

        if matches == 0:
            return 0.0

        k = 0
        for i in range(len_s1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1

        jaro = (matches / len_s1 + matches / len_s2 + (matches - transpositions / 2) / matches) / 3.0

        prefix = 0
        for i in range(min(4, len_s1, len_s2)):
            if s1[i] == s2[i]:
                prefix += 1
            else:
                break

        return jaro + (prefix * 0.1 * (1 - jaro))


class ProbabilisticMatcher(Matcher):
    @property
    def name(self) -> str:
        return "probabilistic"

    def match(self, source: dict[str, Any], target: dict[str, Any]) -> MatchResult:
        features: dict[str, Any] = {}

        nid_match = self._field_equal(source, target, "national_id_hash")
        features["national_id"] = nid_match
        if nid_match:
            return MatchResult(score=1.0, method="probabilistic", matched=True, confidence=1.0, features=features)

        matched_phone = self._field_equal(source, target, "phone")
        matched_dob = self._field_equal(source, target, "date_of_birth")
        matched_name = self._name_exact(source, target)
        matched_gender = self._gender_equal(source, target)

        features["phone"] = matched_phone
        features["dob"] = matched_dob
        features["name"] = matched_name
        features["gender"] = matched_gender

        m_prob = 0.95
        u_prob = 0.05
        log_ratio = 0.0

        if matched_phone:
            log_ratio += self._log2(m_prob / u_prob)
        else:
            log_ratio += self._log2((1 - m_prob) / (1 - u_prob))

        if matched_dob:
            log_ratio += self._log2(m_prob / u_prob)
        else:
            log_ratio += self._log2((1 - m_prob) / (1 - u_prob))

        if matched_name:
            log_ratio += self._log2(m_prob / u_prob)
        else:
            log_ratio += self._log2((1 - m_prob) / (1 - u_prob))

        if matched_gender:
            log_ratio += self._log2(m_prob / u_prob)
        else:
            log_ratio += self._log2((1 - m_prob) / (1 - u_prob))

        score = 1.0 / (1.0 + pow(2.71828, -log_ratio))
        matched = score >= 0.85

        return MatchResult(
            score=round(score, 4),
            method="probabilistic",
            matched=matched,
            confidence=round(score, 4),
            features=features,
        )

    def _log2(self, x: float) -> float:
        import math
        return math.log2(x) if x > 0 else -20.0

    def _field_equal(self, source: dict, target: dict, field: str) -> bool:
        src = source.get(field)
        tgt = target.get(field)
        if not src or not tgt:
            return False
        return str(src).strip().lower() == str(tgt).strip().lower()

    def _name_exact(self, source: dict, target: dict) -> bool:
        src_first = (source.get("first_name") or "").strip().lower()
        src_last = (source.get("last_name") or "").strip().lower()
        tgt_first = (target.get("first_name") or "").strip().lower()
        tgt_last = (target.get("last_name") or "").strip().lower()
        return src_first == tgt_first and src_last == tgt_last

    def _gender_equal(self, source: dict, target: dict) -> bool:
        src = (source.get("gender") or "").strip().lower()
        tgt = (target.get("gender") or "").strip().lower()
        if not src or not tgt:
            return False
        return src[0] == tgt[0]


class MatchingEngine:
    def __init__(self):
        self._matchers: dict[str, Matcher] = {}

    def register(self, matcher: Matcher) -> None:
        self._matchers[matcher.name] = matcher
        logger.info("Matcher registered: %s", matcher.name)

    def unregister(self, name: str) -> None:
        self._matchers.pop(name, None)

    def match(self, source: dict[str, Any], target: dict[str, Any], method: str = "all") -> MatchResult:
        if method == "exact":
            return self._matchers["exact"].match(source, target)
        if method == "fuzzy":
            return self._matchers["fuzzy"].match(source, target)
        if method == "probabilistic":
            return self._matchers["probabilistic"].match(source, target)

        best = MatchResult(score=0.0, method="none")
        for matcher in self._matchers.values():
            result = matcher.match(source, target)
            if result.score > best.score:
                best = result
        return best

    def match_all(self, source: dict[str, Any], targets: list[dict[str, Any]]) -> list[MatchResult]:
        results = []
        for target in targets:
            result = self.match(source, target)
            results.append(result)
        return sorted(results, key=lambda r: r.score, reverse=True)
