from __future__ import annotations

import hashlib
import hmac
import os
import re
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
from app.identity.models.account_request import AccountCreationRequest, AccountRequestStatus
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService
from shared.security.encryption import encrypt_value


class AccountRequestConfigurationError(RuntimeError):
    """Raised when required key material is unavailable; intake must fail closed."""


@dataclass(frozen=True)
class NormalizedAccountRequest:
    email: str | None
    phone: str | None
    display_name: str | None
    requested_account_type: str


class AccountRequestService:
    """Secure, review-gated account intake; approval is a separate governed action."""

    def __init__(self, session: AsyncSession | SyncSessionAsyncFacade) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)
        self._encryption_key = os.getenv("ENCRYPTION_KEY", "")
        self._blind_index_key = os.getenv("NID_HMAC_KEY", "")
        if not self._encryption_key or not self._blind_index_key:
            raise AccountRequestConfigurationError("account request protection keys unavailable")

    @staticmethod
    def normalize(
        *,
        email: str | None,
        phone: str | None,
        display_name: str | None,
        requested_account_type: str,
    ) -> NormalizedAccountRequest:
        normalized_email = email.strip().lower() if email else None
        normalized_phone = re.sub(r"[^0-9+]", "", phone) if phone else None
        normalized_name = " ".join(display_name.split()) if display_name else None
        if not normalized_email and not normalized_phone:
            raise ValueError("email or phone is required")
        if normalized_email and (len(normalized_email) > 200 or "@" not in normalized_email):
            raise ValueError("invalid email")
        if normalized_phone and not (7 <= len(normalized_phone) <= 30):
            raise ValueError("invalid phone")
        if normalized_name and len(normalized_name) > 200:
            raise ValueError("display name is too long")
        if requested_account_type != "human":
            raise ValueError("public account intake supports human requests only")
        return NormalizedAccountRequest(
            email=normalized_email,
            phone=normalized_phone,
            display_name=normalized_name,
            requested_account_type=requested_account_type,
        )

    def _blind_index(self, value: str) -> str:
        return hmac.new(
            self._blind_index_key.encode("utf-8"),
            value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _request_fingerprint(self, normalized: NormalizedAccountRequest) -> str:
        material = "|".join(
            [
                normalized.email or "",
                normalized.phone or "",
                normalized.display_name or "",
                normalized.requested_account_type,
            ],
        )
        return self._blind_index(material)

    async def submit(
        self,
        *,
        email: str | None,
        phone: str | None,
        display_name: str | None,
        requested_account_type: str,
        idempotency_key: str,
        source_ip: str | None,
        request_id: str | None,
        user_agent: str | None,
    ) -> AccountCreationRequest | None:
        normalized = self.normalize(
            email=email,
            phone=phone,
            display_name=display_name,
            requested_account_type=requested_account_type,
        )
        idempotency_hash = self._blind_index(idempotency_key.strip())
        existing_by_key = await self.session.scalar(
            select(AccountCreationRequest).where(
                AccountCreationRequest.idempotency_key_hash == idempotency_hash,
            ),
        )
        if existing_by_key is not None:
            return existing_by_key

        email_lookup = self._blind_index(normalized.email) if normalized.email else None
        phone_lookup = self._blind_index(normalized.phone) if normalized.phone else None
        duplicate_conditions = []
        if email_lookup:
            duplicate_conditions.append(AccountCreationRequest.contact_email_lookup == email_lookup)
        if phone_lookup:
            duplicate_conditions.append(AccountCreationRequest.contact_phone_lookup == phone_lookup)
        if duplicate_conditions:
            duplicate = await self.session.scalar(
                select(AccountCreationRequest).where(
                    AccountCreationRequest.status == AccountRequestStatus.pending_review.value,
                    or_(*duplicate_conditions),
                ),
            )
            if duplicate is not None:
                await self.audit.record(
                    AuditEventInput(
                        event_type="account_request_duplicate_suppressed",
                        category="account_request",
                        action="account_request.duplicate_suppressed",
                        target_type="account_creation_request",
                        decision="deny",
                        reason_code="duplicate_pending_request",
                        request_id=request_id,
                        source="public_account_request",
                        data_classification="PERSONAL_SENSITIVE",
                        metadata={"status": AccountRequestStatus.pending_review.value},
                        outcome="denied",
                    ),
                )
                await self.session.commit()
                return None

        account_request = AccountCreationRequest(
            request_uuid=str(uuid.uuid4()),
            status=AccountRequestStatus.pending_review.value,
            requested_account_type=normalized.requested_account_type,
            contact_email_encrypted=(
                encrypt_value(normalized.email, self._encryption_key) if normalized.email else None
            ),
            contact_email_lookup=email_lookup,
            contact_phone_encrypted=(
                encrypt_value(normalized.phone, self._encryption_key) if normalized.phone else None
            ),
            contact_phone_lookup=phone_lookup,
            display_name_encrypted=(
                encrypt_value(normalized.display_name, self._encryption_key)
                if normalized.display_name
                else None
            ),
            idempotency_key_hash=idempotency_hash,
            request_fingerprint=self._request_fingerprint(normalized),
            source_ip_hash=self._blind_index(source_ip) if source_ip else None,
            is_active=True,
        )
        self.session.add(account_request)
        await self.session.flush()
        await self.audit.record(
            AuditEventInput(
                event_type="account_request_submitted",
                category="account_request",
                action="account_request.submit",
                target_type="account_creation_request",
                target_id=account_request.id,
                decision="allow",
                reason_code="pending_review",
                request_id=request_id,
                source="public_account_request",
                data_classification="PERSONAL_SENSITIVE",
                changes={"status": AccountRequestStatus.pending_review.value},
                metadata={"requested_account_type": normalized.requested_account_type},
                user_agent=user_agent,
                outcome="success",
            ),
        )
        await self.session.commit()
        return account_request

    @staticmethod
    def public_result(account_request: AccountCreationRequest | None) -> dict[str, Any]:
        return {
            "accepted": True,
            "status": AccountRequestStatus.pending_review.value,
            "request_id": account_request.request_uuid if account_request else None,
            "message": "Your request was received for review.",
        }
