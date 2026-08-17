from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.clinical_gateway.context import (
    ClinicalGatewayBlocked,
    ClinicalGatewayContext,
    ClinicalGatewayContextResolver,
)
from app.clinical_gateway.contracts import (
    ClinicalPageRequest,
    ClinicalReadEnvelope,
    OrderRead,
    PatientRead,
    ResultRead,
)
from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationRequest,
)
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService
from app.services.order_service import get_order_by_id
from app.services.order_service import list_orders
from app.services.patient_service import list_patients


class ClinicalGatewayAuditFailure(RuntimeError):
    """Raised when the canonical audit event cannot be written."""


class ClinicalGatewayInvalidCursor(ValueError):
    """Raised when a cursor is invalid, expired by scope, or tampered with."""


_ResultT = TypeVar("_ResultT")


@dataclass(frozen=True)
class ClinicalReadResult:
    items: list[PatientRead] | list[OrderRead] | list[ResultRead]
    total: int
    next_cursor: str | None


class ClinicalCursorCodec:
    """Signed, scope-bound offset cursor; no client-controlled IDs are trusted."""

    def __init__(self) -> None:
        self._secret = os.getenv("SECRET_KEY", "")

    def encode(self, *, resource: str, workspace_id: str, limit: int, offset: int) -> str:
        if not self._secret:
            raise ClinicalGatewayInvalidCursor("cursor signing key unavailable")
        payload = {
            "resource": resource,
            "workspace_id": workspace_id,
            "limit": limit,
            "offset": offset,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        encoded = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        signature = hmac.new(self._secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        return f"{encoded}.{signature}"

    def decode(self, *, cursor: str, resource: str, workspace_id: str, limit: int) -> int:
        if not self._secret or "." not in cursor:
            raise ClinicalGatewayInvalidCursor("invalid cursor")
        encoded, signature = cursor.rsplit(".", 1)
        expected = hmac.new(self._secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ClinicalGatewayInvalidCursor("invalid cursor")
        padded = encoded + "=" * (-len(encoded) % 4)
        try:
            payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ClinicalGatewayInvalidCursor("invalid cursor") from exc
        offset = payload.get("offset")
        if (
            payload.get("resource") != resource
            or payload.get("workspace_id") != workspace_id
            or payload.get("limit") != limit
            or not isinstance(offset, int)
            or offset < 0
        ):
            raise ClinicalGatewayInvalidCursor("cursor scope mismatch")
        return offset


class ClinicalGatewayService:
    """Canonical, read-only clinical gateway over existing legacy services."""

    PERMISSIONS = {"patients": "patients.read", "orders": "orders.read", "results": "results.read"}
    RESOURCE_TYPES = {"patients": "clinical_patient", "orders": "clinical_order", "results": "clinical_result"}

    def __init__(self, db: Session) -> None:
        self.db = db
        self.facade = SyncSessionAsyncFacade(db)
        self.audit = CanonicalAuditService(self.facade)
        self.cursor = ClinicalCursorCodec()
        self.context_resolver = ClinicalGatewayContextResolver(db)

    def list_patients(
        self,
        *,
        context: ClinicalGatewayContext,
        request_id: UUID,
        correlation_id: UUID,
        params: ClinicalPageRequest,
    ) -> ClinicalReadEnvelope[PatientRead]:
        resource = "patients"
        offset = self._offset(params, resource, context.scope.niam_workspace_id)
        self._authorize_and_audit(
            context=context,
            resource=resource,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        result = list_patients(
            self.db,
            lab_id=context.scope.legacy_lab_id,
            search=params.search,
            skip=offset,
            limit=params.limit,
            scope=context.scope,
        )
        items = [
            PatientRead(
                id=str(item["id"]),
                display_name=item["full_name"],
                birth_date=item.get("birth_date"),
                gender=item.get("gender"),
                created_at=item.get("created_at"),
            )
            for item in result["patients"]
        ]
        next_cursor = self._next_cursor(
            resource=resource,
            workspace_id=context.scope.niam_workspace_id,
            limit=params.limit,
            offset=offset,
            total=result["total"],
        )
        return ClinicalReadEnvelope[PatientRead](
            request_id=request_id,
            correlation_id=correlation_id,
            workspace_context=self._workspace_context(context),
            items=items,
            limit=params.limit,
            next_cursor=next_cursor,
            total=result["total"],
        )

    def list_orders(
        self,
        *,
        context: ClinicalGatewayContext,
        request_id: UUID,
        correlation_id: UUID,
        params: ClinicalPageRequest,
    ) -> ClinicalReadEnvelope[OrderRead]:
        resource = "orders"
        offset = self._offset(params, resource, context.scope.niam_workspace_id)
        self._authorize_and_audit(
            context=context,
            resource=resource,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        result = list_orders(
            self.db,
            lab_id=context.scope.legacy_lab_id,
            user_role=context.legacy_user.role,
            user_id=context.legacy_user.id,
            skip=offset,
            limit=params.limit,
            search=params.search,
            scope=context.scope,
            include_results=False,
        )
        items = [
            OrderRead(
                id=str(item["id"]),
                patient_display_name=item.get("patient_name"),
                practitioner_display_name=item.get("doctor_name"),
                status=item["status"],
                test_count=item.get("results_count", 0),
                created_at=item.get("created_at"),
            )
            for item in result["orders"]
        ]
        next_cursor = self._next_cursor(
            resource=resource,
            workspace_id=context.scope.niam_workspace_id,
            limit=params.limit,
            offset=offset,
            total=result["total"],
        )
        return ClinicalReadEnvelope[OrderRead](
            request_id=request_id,
            correlation_id=correlation_id,
            workspace_context=self._workspace_context(context),
            items=items,
            limit=params.limit,
            next_cursor=next_cursor,
            total=result["total"],
        )

    def list_results(
        self,
        *,
        context: ClinicalGatewayContext,
        request_id: UUID,
        correlation_id: UUID,
        order_id: int,
    ) -> ClinicalReadEnvelope[ResultRead]:
        resource = "results"
        self._authorize_and_audit(
            context=context,
            resource=resource,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        result = get_order_by_id(
            db=self.db,
            order_id=order_id,
            lab_id=context.scope.legacy_lab_id,
            user_role=context.legacy_user.role,
            user_id=context.legacy_user.id,
            scope=context.scope,
        )
        if result is None:
            raise ClinicalGatewayBlocked("not_found")
        items = [
            ResultRead(
                id=str(item["id"]),
                order_id=str(order_id),
                test_name=item["test_name"],
                value=item.get("value"),
                value_text=item.get("value_text"),
                unit=item.get("unit"),
                normal_range_low=item.get("normal_range_low"),
                normal_range_high=item.get("normal_range_high"),
                flag=item.get("flag"),
                interpretation=item.get("interpretation"),
                created_at=item.get("created_at"),
            )
            for item in result.get("results", [])
        ]
        return ClinicalReadEnvelope[ResultRead](
            request_id=request_id,
            correlation_id=correlation_id,
            workspace_context=self._workspace_context(context),
            items=items,
            limit=max(len(items), 1),
            next_cursor=None,
            total=len(items),
        )

    def _authorize_and_audit(
        self,
        *,
        context: ClinicalGatewayContext,
        resource: str,
        request_id: UUID,
        correlation_id: UUID,
    ) -> None:
        request = AuthorizationRequest(
            subject_account_id=context.actor.account.id,
            action="read",
            resource_type=self.RESOURCE_TYPES[resource],
            permission_key=self.PERMISSIONS[resource],
            organization_id=context.scope.niam_organization_id,
            facility_id=context.scope.niam_facility_id,
            workspace_id=context.scope.niam_workspace_id,
            membership_id=context.membership.id,
            resource_context={
                "exists": True,
                "organization_id": context.scope.niam_organization_id,
                "facility_id": context.scope.niam_facility_id,
                "workspace_id": context.scope.niam_workspace_id,
                "operational_facility_id": context.scope.operational_facility_id,
                "operational_organization_id": context.scope.operational_organization_id,
            },
            sensitivity="high",
        )
        decision = self._run(
            AuthorizationDecisionService(self.facade).authorize(
                AuthorizationActor(account=context.actor.account, session=context.actor.session),
                request,
            ),
        )
        self._audit(
            context=context,
            resource=resource,
            request_id=request_id,
            correlation_id=correlation_id,
            decision=decision.decision.value,
            reason_code=decision.reason_code.value,
        )
        if not decision.allowed:
            raise ClinicalGatewayBlocked("permission_denied")

    def _audit(
        self,
        *,
        context: ClinicalGatewayContext,
        resource: str,
        request_id: UUID,
        correlation_id: UUID,
        decision: str,
        reason_code: str,
    ) -> None:
        try:
            self._run(
                self.audit.record(
                    AuditEventInput(
                        event_type="clinical_gateway_access",
                        category="clinical_access",
                        action=f"{resource}.read",
                        actor_id=context.actor.account.id,
                        actor_identity_id=context.actor.account.identity_id,
                        organization_id=context.scope.niam_organization_id,
                        facility_id=context.scope.niam_facility_id,
                        workspace_id=context.scope.niam_workspace_id,
                        target_type=self.RESOURCE_TYPES[resource],
                        decision=decision,
                        reason_code=reason_code,
                        request_id=str(request_id),
                        correlation_id=str(correlation_id),
                        session_id=context.actor.session.id,
                        source="clinical_gateway",
                        data_classification="CLINICAL_SENSITIVE",
                        metadata={"scope_mapping_version": context.scope.scope_mapping_version},
                        outcome="success" if decision == "allow" else "denied",
                    ),
                ),
            )
        except Exception as exc:
            raise ClinicalGatewayAuditFailure("canonical audit unavailable") from exc

    def _offset(self, params: ClinicalPageRequest, resource: str, workspace_id: str) -> int:
        if params.cursor is None:
            return 0
        try:
            return self.cursor.decode(
                cursor=params.cursor,
                resource=resource,
                workspace_id=workspace_id,
                limit=params.limit,
            )
        except ClinicalGatewayInvalidCursor as exc:
            raise ClinicalGatewayBlocked("invalid_cursor") from exc

    def _next_cursor(
        self, *, resource: str, workspace_id: str, limit: int, offset: int, total: int
    ) -> str | None:
        if offset + limit >= total:
            return None
        return self.cursor.encode(
            resource=resource, workspace_id=workspace_id, limit=limit, offset=offset + limit
        )

    @staticmethod
    def _workspace_context(context: ClinicalGatewayContext) -> dict[str, str | None]:
        return {
            "organization_id": context.scope.niam_organization_id,
            "facility_id": context.scope.niam_facility_id,
            "workspace_id": context.scope.niam_workspace_id,
            "department_id": context.workspace.department_id,
        }

    @staticmethod
    def _run(awaitable: Awaitable[_ResultT]) -> _ResultT:
        import asyncio

        return asyncio.run(awaitable)
