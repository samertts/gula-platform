from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.research_platform.privacy")


class DeIdentificationService:
    def __init__(self):
        self._salt = "research-deid-salt"

    def deidentify_record(self, record: dict, phi_fields: list[str] | None = None) -> dict:
        fields = phi_fields or ["first_name", "last_name", "full_name", "national_id", "phone", "email", "address"]
        result = record.copy()
        for field in fields:
            if field in result:
                result[field] = self._mask_value(result[field])
        return result

    def deidentify_batch(self, records: list[dict], phi_fields: list[str] | None = None) -> list[dict]:
        return [self.deidentify_record(r, phi_fields) for r in records]

    @staticmethod
    def _mask_value(value: Any) -> str:
        s = str(value)
        if len(s) <= 3:
            return "***"
        return s[0] + "***" + s[-1] if len(s) > 4 else s[0] + "***"

    def safe_harbor(self, record: dict) -> dict:
        safe = record.copy()
        safe.pop("date_of_birth", None)
        safe.pop("age_years", None)
        if safe.get("age_years") is not None and safe["age_years"] >= 90:
            safe["age_group"] = "90+"
        safe.pop("postal_code", None)
        safe.pop("phone", None)
        safe.pop("email", None)
        safe.pop("national_id", None)
        safe.pop("health_id", None)
        safe.pop("full_name", None)
        safe.pop("first_name", None)
        safe.pop("last_name", None)
        safe.pop("address", None)
        return safe

    def expert_determination(self, record: dict, expert_approval_id: str) -> dict:
        return {**record, "_deid_method": "expert_determination", "_expert_approval": expert_approval_id}


class PseudonymizationService:
    def __init__(self):
        self._pseudonym_map: dict[str, str] = {}
        self._hmac_key = "research-pseudo-key"

    def pseudonymize(self, value: str, domain: str = "patient") -> str:
        key = f"{domain}:{value}"
        if key in self._pseudonym_map:
            return self._pseudonym_map[key]
        pseudo = hashlib.sha256(f"{value}{self._hmac_key}{domain}".encode()).hexdigest()[:16]
        pseudo_id = f"PSEUDO-{pseudo.upper()}"
        self._pseudonym_map[key] = pseudo_id
        return pseudo_id

    def pseudonymize_record(self, record: dict, fields: list[str] | None = None) -> dict:
        targets = fields or ["patient_ulid", "national_id", "health_id"]
        result = record.copy()
        for field in targets:
            if result.get(field):
                result[field] = self.pseudonymize(str(result[field]), field)
        return result

    def pseudonymize_batch(self, records: list[dict], fields: list[str] | None = None) -> list[dict]:
        return [self.pseudonymize_record(r, fields) for r in records]

    def reidentify(self, pseudonym: str) -> str | None:
        for key, val in self._pseudonym_map.items():
            if val == pseudonym:
                return key.split(":", 1)[1] if ":" in key else None
        return None

    def clear_mapping(self) -> None:
        self._pseudonym_map.clear()
        logger.info("Pseudonym mapping cleared")


class DifferentialPrivacy:
    def __init__(self):
        self._epsilon: float = 1.0
        self._budget_tracker: dict[str, float] = {}

    def set_epsilon(self, epsilon: float) -> None:
        self._epsilon = epsilon
        logger.info("Differential privacy epsilon set to: %s", epsilon)

    def add_laplace_noise(self, value: float, sensitivity: float = 1.0) -> float:
        import random

        scale = sensitivity / (self._epsilon or 0.01)
        noise = random.laplace(0, scale)
        return value + noise

    def check_budget(self, query_id: str) -> bool:
        spent = self._budget_tracker.get(query_id, 0)
        return spent < self._epsilon

    def consume_budget(self, query_id: str, amount: float) -> None:
        self._budget_tracker[query_id] = self._budget_tracker.get(query_id, 0) + amount
        logger.debug("DP budget consumed for %s: %.2f/%.2f", query_id, self._budget_tracker[query_id], self._epsilon)

    def reset_budget(self, query_id: str) -> None:
        self._budget_tracker.pop(query_id, None)

    def noisy_count(self, actual_count: int) -> int:
        noise = self.add_laplace_noise(0, 1.0)
        return max(0, round(actual_count + noise))

    def noisy_mean(self, values: list[float]) -> float:
        if not values:
            return 0.0
        actual = sum(values) / len(values)
        return self.add_laplace_noise(actual, sensitivity=max(values) - min(values) if values else 1.0)


class ConsentEnforcement:
    def __init__(self):
        self._consents: dict[str, list[dict]] = {}

    def record_consent(
        self,
        patient_ulid: str,
        project_id: str,
        scope: list[str] | None = None,
        status: str = "granted",
    ) -> dict[str, Any]:
        consent = {
            "patient_ulid": patient_ulid,
            "project_id": project_id,
            "scope": scope or ["all"],
            "status": status,
            "granted_at": datetime.now(UTC).isoformat() if status == "granted" else None,
            "revoked_at": None,
        }
        self._consents.setdefault(patient_ulid, []).append(consent)
        logger.info("Consent recorded: %s -> %s (%s)", patient_ulid, project_id, status)
        return consent

    def check_access(self, patient_ulid: str, project_id: str, data_type: str = "all") -> bool:
        consents = self._consents.get(patient_ulid, [])
        for c in consents:
            if c["project_id"] == project_id and c["status"] == "granted":
                if "all" in c["scope"] or data_type in c["scope"]:
                    return True
        return False

    def revoke_consent(self, patient_ulid: str, project_id: str) -> bool:
        consents = self._consents.get(patient_ulid, [])
        for c in consents:
            if c["project_id"] == project_id and c["status"] == "granted":
                c["status"] = "revoked"
                c["revoked_at"] = datetime.now(UTC).isoformat()
                logger.info("Consent revoked: %s -> %s", patient_ulid, project_id)
                return True
        return False

    def get_consents(self, patient_ulid: str) -> list[dict]:
        return self._consents.get(patient_ulid, [])

    def check_batch_access(self, patient_ulids: list[str], project_id: str) -> dict[str, bool]:
        return {pid: self.check_access(pid, project_id) for pid in patient_ulids}


class ResearchApprovalWorkflow:
    def __init__(self):
        self._requests: dict[str, dict] = {}

    def submit(self, project_id: str, researcher_id: str, purpose: str) -> dict[str, Any]:
        import uuid

        request_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
        req = {
            "request_id": request_id,
            "project_id": project_id,
            "researcher_id": researcher_id,
            "purpose": purpose,
            "status": "pending",
            "submitted_at": datetime.now(UTC).isoformat(),
            "reviewed_by": None,
            "reviewed_at": None,
            "notes": "",
        }
        self._requests[request_id] = req
        logger.info("Research approval request submitted: %s", request_id)
        return req

    def approve(self, request_id: str, reviewer_id: str, notes: str = "") -> dict | None:
        req = self._requests.get(request_id)
        if req and req["status"] == "pending":
            req["status"] = "approved"
            req["reviewed_by"] = reviewer_id
            req["reviewed_at"] = datetime.now(UTC).isoformat()
            req["notes"] = notes
            logger.info("Research approval granted: %s", request_id)
        return req

    def reject(self, request_id: str, reviewer_id: str, reason: str) -> dict | None:
        req = self._requests.get(request_id)
        if req and req["status"] == "pending":
            req["status"] = "rejected"
            req["reviewed_by"] = reviewer_id
            req["reviewed_at"] = datetime.now(UTC).isoformat()
            req["notes"] = reason
            logger.info("Research approval rejected: %s", request_id)
        return req

    def get(self, request_id: str) -> dict | None:
        return self._requests.get(request_id)

    def list_by_status(self, status: str = "pending") -> list[dict]:
        return [r for r in self._requests.values() if r["status"] == status]


class EthicsReviewWorkflow:
    def __init__(self):
        self._reviews: dict[str, dict] = {}

    def submit_for_review(
        self,
        project_id: str,
        protocol_document: str = "",
        researcher_id: str = "",
    ) -> dict[str, Any]:
        import uuid

        review_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
        review = {
            "review_id": review_id,
            "project_id": project_id,
            "protocol_document": protocol_document,
            "researcher_id": researcher_id,
            "status": "submitted",
            "submitted_at": datetime.now(UTC).isoformat(),
            "committee_members": [],
            "decisions": [],
            "final_decision": None,
            "approved_at": None,
        }
        self._reviews[review_id] = review
        logger.info("Ethics review submitted: %s", review_id)
        return review

    def assign_reviewer(self, review_id: str, reviewer_id: str) -> dict | None:
        review = self._reviews.get(review_id)
        if review:
            review["committee_members"].append(reviewer_id)
        return review

    def record_decision(self, review_id: str, reviewer_id: str, decision: str, comments: str = "") -> dict | None:
        review = self._reviews.get(review_id)
        if review:
            review["decisions"].append({
                "reviewer_id": reviewer_id,
                "decision": decision,
                "comments": comments,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            decisions = review["decisions"]
            if all(d["decision"] == "approve" for d in decisions) and len(decisions) >= 1:
                review["final_decision"] = "approved"
                review["status"] = "approved"
                review["approved_at"] = datetime.now(UTC).isoformat()
            elif any(d["decision"] == "reject" for d in decisions):
                review["final_decision"] = "rejected"
                review["status"] = "rejected"
        return review

    def get(self, review_id: str) -> dict | None:
        return self._reviews.get(review_id)

    def list_by_status(self, status: str = "submitted") -> list[dict]:
        return [r for r in self._reviews.values() if r.get("status") == status]
