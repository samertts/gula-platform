from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.clinical_gateway.session_facade import SyncSessionAsyncFacade
from app.identity.models.account import Account, AccountStatus
from app.identity.models.account_request import AccountCreationRequest, AccountRequestStatus
from app.identity.models.audit import AuditAction
from app.identity.models.identity import IdentityRecord, IdentityType
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.person import Person
from app.identity.models.verification_record import VerificationRecord, VerificationRecordStatus
from app.identity.services.account_lifecycle_service import (
    AccountLifecycleService,
    InvalidAccountTransition,
)
from app.identity.services.audit_service import AuditService
from app.identity.services.canonical_audit import AuditEventInput, CanonicalAuditService
from app.identity.services.verification_record_service import VerificationRecordService
from app.notifications.service import get_service
from app.security.auth import hash_password
from app.security.redis_client import cache
from shared.security.encryption import decrypt_value, encrypt_value


class AccountRequestConfigurationError(RuntimeError):
    """Raised when required key material is unavailable; intake must fail closed."""


class AccountRequestStateError(ValueError):
    """Raised when a request lifecycle transition is not legal."""


class VerificationProviderUnavailable(RuntimeError):
    """Raised when the configured notification provider cannot deliver an OTP."""


class AccountRequestConflict(ValueError):
    """Raised when an idempotent request conflicts with another account/request."""


@dataclass(frozen=True)
class NormalizedAccountRequest:
    email: str | None
    phone: str | None
    display_name: str | None
    requested_account_type: str


REQUEST_TRANSITIONS: dict[str, frozenset[str]] = {
    AccountRequestStatus.pending_review.value: frozenset({
        AccountRequestStatus.under_review.value,
        AccountRequestStatus.rejected.value,
        AccountRequestStatus.expired.value,
    }),
    AccountRequestStatus.under_review.value: frozenset({
        AccountRequestStatus.pending_verification.value,
        AccountRequestStatus.rejected.value,
        AccountRequestStatus.expired.value,
    }),
    AccountRequestStatus.pending_verification.value: frozenset({
        AccountRequestStatus.verified.value,
        AccountRequestStatus.rejected.value,
        AccountRequestStatus.expired.value,
    }),
    AccountRequestStatus.verified.value: frozenset({
        AccountRequestStatus.pending_approval.value,
        AccountRequestStatus.rejected.value,
        AccountRequestStatus.expired.value,
    }),
    AccountRequestStatus.pending_approval.value: frozenset({
        AccountRequestStatus.approved.value,
        AccountRequestStatus.rejected.value,
        AccountRequestStatus.expired.value,
    }),
    AccountRequestStatus.approved.value: frozenset(),
    AccountRequestStatus.rejected.value: frozenset(),
    AccountRequestStatus.expired.value: frozenset(),
    AccountRequestStatus.cancelled.value: frozenset(),
}

_OTP_TTL_SECONDS = 15 * 60
_OTP_MAX_ATTEMPTS = 5
_OTP_MAX_RESENDS = 3
_OTP_RESEND_WINDOW_SECONDS = 60
_REQUEST_TTL = timedelta(days=30)
_ACTIVATION_TTL = timedelta(hours=24)


class AccountRequestService:
    """Secure, review-gated account intake and canonical account lifecycle."""

    def __init__(self, session: AsyncSession | SyncSessionAsyncFacade) -> None:
        self.session = session
        self.audit = CanonicalAuditService(session)
        self._encryption_key = os.getenv("ENCRYPTION_KEY", "")
        self._blind_index_key = os.getenv("NID_HMAC_KEY", "")
        if not self._encryption_key or not self._blind_index_key:
            raise AccountRequestConfigurationError("account request protection keys unavailable")
        try:
            Fernet(self._encryption_key.encode("utf-8"))
        except Exception as exc:
            raise AccountRequestConfigurationError(
                "account request encryption is unavailable",
            ) from exc

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

    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        return target in REQUEST_TRANSITIONS.get(current, frozenset())

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

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

    def _decrypt_optional(self, value: str | None) -> str | None:
        return decrypt_value(value, self._encryption_key) if value else None

    def _encrypt_optional_reason(self, value: str | None) -> str | None:
        return encrypt_value(value, self._encryption_key) if value else None

    @staticmethod
    def _otp_key(request_uuid: str) -> str:
        digest = hashlib.sha256(request_uuid.encode("utf-8")).hexdigest()
        return f"niam:account-request:otp:{digest}"

    @staticmethod
    def _otp_attempt_key(request_uuid: str) -> str:
        digest = hashlib.sha256(request_uuid.encode("utf-8")).hexdigest()
        return f"niam:account-request:otp-attempts:{digest}"

    @staticmethod
    def _otp_resend_key(request_uuid: str) -> str:
        digest = hashlib.sha256(request_uuid.encode("utf-8")).hexdigest()
        return f"niam:account-request:otp-resends:{digest}"

    @staticmethod
    def _activation_token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def _get_request(self, request_uuid: str, *, for_update: bool = False) -> AccountCreationRequest | None:
        statement = select(AccountCreationRequest).where(
            AccountCreationRequest.request_uuid == request_uuid,
        )
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def _audit_event(
        self,
        *,
        event_type: str,
        action: str,
        request: AccountCreationRequest,
        actor_id: str | None,
        decision: str,
        reason_code: str,
        outcome: str = "success",
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        await self.audit.record(
            AuditEventInput(
                event_type=event_type,
                category="account_lifecycle",
                action=action,
                actor_id=actor_id,
                target_type="account_creation_request",
                target_id=request.id,
                decision=decision,
                reason_code=reason_code,
                request_id=request_id,
                source="account_lifecycle",
                data_classification="PERSONAL_SENSITIVE",
                changes=changes,
                metadata=metadata,
                outcome=outcome,
            ),
        )

    async def _transition_request(
        self,
        request: AccountCreationRequest,
        target: AccountRequestStatus,
        *,
        actor_id: str | None,
        reason_code: str,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AccountCreationRequest:
        current = str(request.status)
        if not self.can_transition(current, target.value):
            raise AccountRequestStateError(f"Illegal account request transition: {current} -> {target.value}")
        request.status = target.value
        if target in {
            AccountRequestStatus.under_review,
            AccountRequestStatus.rejected,
            AccountRequestStatus.expired,
            AccountRequestStatus.pending_approval,
            AccountRequestStatus.approved,
        }:
            request.reviewed_by_account_id = actor_id or request.reviewed_by_account_id
            request.reviewed_at = self._now()
        await self._audit_event(
            event_type=f"account_request_{target.value}",
            action=f"account_request.{target.value}",
            request=request,
            actor_id=actor_id,
            decision="allow",
            reason_code=reason_code,
            request_id=request_id,
            changes={"status": {"from": current, "to": target.value}},
            metadata=metadata,
        )
        return request

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
        if len(idempotency_key.strip()) < 16:
            raise ValueError("idempotency key is too short")
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
                    AccountCreationRequest.status.in_(
                        [
                            AccountRequestStatus.pending_review.value,
                            AccountRequestStatus.under_review.value,
                            AccountRequestStatus.pending_verification.value,
                            AccountRequestStatus.verified.value,
                            AccountRequestStatus.pending_approval.value,
                        ],
                    ),
                    or_(*duplicate_conditions),
                ),
            )
            if duplicate is not None:
                await self._audit_event(
                    event_type="account_request_duplicate_suppressed",
                    action="account_request.duplicate_suppressed",
                    request=duplicate,
                    actor_id=None,
                    decision="deny",
                    reason_code="duplicate_pending_request",
                    request_id=request_id,
                    outcome="denied",
                    metadata={"status": duplicate.status},
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
            expires_at=self._now() + _REQUEST_TTL,
            is_active=True,
        )
        self.session.add(account_request)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            # A concurrent request can win the unique idempotency race. The
            # caller receives a conflict-safe response instead of a duplicate.
            raise AccountRequestConflict("Account request already exists") from exc
        await self._audit_event(
            event_type="account_request_submitted",
            action="account_request.submit",
            request=account_request,
            actor_id=None,
            decision="allow",
            reason_code="pending_review",
            request_id=request_id,
            changes={"status": AccountRequestStatus.pending_review.value},
            metadata={"requested_account_type": normalized.requested_account_type},
        )
        await self.session.commit()
        return account_request

    async def start_review(self, request_uuid: str, actor_id: str) -> AccountCreationRequest:
        request = await self._get_request(request_uuid, for_update=True)
        if request is None:
            raise LookupError("Account request not found")
        if request.expires_at and request.expires_at <= self._now():
            await self._transition_request(
                request,
                AccountRequestStatus.expired,
                actor_id=actor_id,
                reason_code="request_expired",
            )
            await self.session.commit()
            raise AccountRequestStateError("Account request has expired")
        await self._transition_request(
            request,
            AccountRequestStatus.under_review,
            actor_id=actor_id,
            reason_code="manual_review_started",
        )
        await self.session.commit()
        return request

    async def start_verification(self, request_uuid: str, *, request_id: str | None = None) -> AccountCreationRequest:
        request = await self._get_request(request_uuid, for_update=True)
        if request is None:
            raise LookupError("Account request not found")
        if request.expires_at and request.expires_at <= self._now():
            await self._transition_request(
                request,
                AccountRequestStatus.expired,
                actor_id=None,
                reason_code="request_expired",
                request_id=request_id,
            )
            await self.session.commit()
            raise AccountRequestStateError("Account request has expired")
        if request.verification_locked_at:
            raise AccountRequestStateError("Verification is locked")
        is_resend = request.status == AccountRequestStatus.pending_verification.value
        if request.status not in {
            AccountRequestStatus.under_review.value,
            AccountRequestStatus.pending_verification.value,
        }:
            raise AccountRequestStateError("Account request is not ready for verification")
        if is_resend:
            resend_count = int(cache.get(self._otp_resend_key(request_uuid)) or "0")
            if resend_count >= _OTP_MAX_RESENDS:
                raise AccountRequestStateError("Verification resend is throttled")
            resend_count = cache.incr(self._otp_resend_key(request_uuid))
            if resend_count == 1:
                cache.expire(self._otp_resend_key(request_uuid), _OTP_RESEND_WINDOW_SECONDS)

        email = self._decrypt_optional(request.contact_email_encrypted)
        phone = self._decrypt_optional(request.contact_phone_encrypted)
        recipient = email or phone
        channel = "email" if email else "sms"
        if not recipient:
            raise VerificationProviderUnavailable("No verified contact provider is available")

        code = f"{secrets.randbelow(1_000_000):06d}"
        message = "Your GULA verification code is valid for 15 minutes."
        notification = (
            get_service().send_email(recipient, "GULA account verification", f"{message} Code: {code}")
            if channel == "email"
            else get_service().send_sms(recipient, f"{message} Code: {code}")
        )
        if not notification.success:
            raise VerificationProviderUnavailable("Verification provider did not accept the message")

        cache.set(
            self._otp_key(request_uuid),
            json.dumps({"digest": hashlib.sha256(code.encode()).hexdigest(), "channel": channel}),
            ex=_OTP_TTL_SECONDS,
        )
        cache.set(
            self._otp_attempt_key(request_uuid),
            str(request.verification_attempts or 0),
            ex=_OTP_TTL_SECONDS,
        )
        if is_resend:
            await self._audit_event(
                event_type="account_request_verification_resent",
                action="account_request.verification_resent",
                request=request,
                actor_id=None,
                decision="allow",
                reason_code="resend_allowed",
                request_id=request_id,
                metadata={"channel": channel},
            )
        else:
            await self._transition_request(
                request,
                AccountRequestStatus.pending_verification,
                actor_id=None,
                reason_code="verification_started",
                request_id=request_id,
                metadata={"channel": channel},
            )
        await self.session.commit()
        return request

    async def confirm_verification(
        self,
        request_uuid: str,
        code: str,
        *,
        request_id: str | None = None,
    ) -> AccountCreationRequest:
        request = await self._get_request(request_uuid, for_update=True)
        entry = cache.get(self._otp_key(request_uuid))
        if request is None or request.status != AccountRequestStatus.pending_verification.value or not entry:
            raise AccountRequestStateError("Verification is invalid or expired")
        if request.verification_locked_at:
            raise AccountRequestStateError("Verification is locked")
        attempts = max(
            int(cache.get(self._otp_attempt_key(request_uuid)) or "0"),
            int(request.verification_attempts or 0),
        )
        if attempts >= _OTP_MAX_ATTEMPTS:
            request.verification_locked_at = self._now()
            request.verification_failure_reason_code = "too_many_attempts"
            cache.delete(self._otp_key(request_uuid))
            await self._audit_event(
                event_type="account_request_verification_locked",
                action="account_request.verification_locked",
                request=request,
                actor_id=None,
                decision="deny",
                reason_code="too_many_attempts",
                request_id=request_id,
                outcome="denied",
            )
            await self.session.commit()
            raise AccountRequestStateError("Too many verification attempts")
        try:
            stored = json.loads(entry)
        except (TypeError, json.JSONDecodeError):
            stored = {}
        digest = hashlib.sha256(code.encode()).hexdigest()
        if not hmac.compare_digest(str(stored.get("digest", "")), digest):
            request.verification_attempts = attempts + 1
            cache.set(self._otp_attempt_key(request_uuid), str(request.verification_attempts), ex=_OTP_TTL_SECONDS)
            if request.verification_attempts >= _OTP_MAX_ATTEMPTS:
                request.verification_locked_at = self._now()
                request.verification_failure_reason_code = "too_many_attempts"
                cache.delete(self._otp_key(request_uuid))
                event_type = "account_request_verification_locked"
                action = "account_request.verification_locked"
                reason_code = "too_many_attempts"
            else:
                request.verification_failure_reason_code = "invalid_verification_code"
                event_type = "account_request_verification_failed"
                action = "account_request.verification_failed"
                reason_code = "invalid_verification_code"
            await self._audit_event(
                event_type=event_type,
                action=action,
                request=request,
                actor_id=None,
                decision="deny",
                reason_code=reason_code,
                request_id=request_id,
                outcome="denied",
            )
            await self.session.commit()
            raise AccountRequestStateError(
                "Too many verification attempts" if request.verification_locked_at else "Verification is invalid or expired",
            )

        cache.delete(self._otp_key(request_uuid))
        cache.delete(self._otp_attempt_key(request_uuid))
        cache.delete(self._otp_resend_key(request_uuid))
        request.verification_method = str(stored.get("channel", ""))
        request.verification_provider = f"notification:{request.verification_method}"
        request.verification_reference = None
        request.verification_failure_reason_code = None
        request.verified_at = self._now()
        await self._transition_request(
            request,
            AccountRequestStatus.verified,
            actor_id=None,
            reason_code="verification_passed",
            request_id=request_id,
            metadata={"method": request.verification_method},
        )
        await self.session.commit()
        return request

    async def approve(self, request_uuid: str, actor_id: str) -> tuple[AccountCreationRequest, Account]:
        request = await self._get_request(request_uuid, for_update=True)
        if request is None:
            raise LookupError("Account request not found")
        if request.account_id:
            account = await self.session.get(Account, request.account_id)
            if account is None:
                raise AccountRequestConflict("Account request points to a missing account")
            return request, account
        if request.status == AccountRequestStatus.verified.value:
            await self._transition_request(
                request,
                AccountRequestStatus.pending_approval,
                actor_id=actor_id,
                reason_code="approval_review_started",
            )
        if request.status != AccountRequestStatus.pending_approval.value:
            raise AccountRequestStateError("Account request is not verified and ready for approval")

        email = self._decrypt_optional(request.contact_email_encrypted)
        phone = self._decrypt_optional(request.contact_phone_encrypted)
        display_name = self._decrypt_optional(request.display_name_encrypted) or "GULA Account"
        duplicate_conditions = []
        if email:
            duplicate_conditions.append(Account.email == email)
        if phone:
            duplicate_conditions.append(Account.phone == phone)
        if duplicate_conditions:
            duplicate = await self.session.scalar(select(Account).where(or_(*duplicate_conditions)))
            if duplicate is not None:
                raise AccountRequestConflict("A matching account already exists")

        names = display_name.split()
        given_name = names[0][:100]
        family_name = (names[-1] if len(names) > 1 else names[0])[:100]
        person = Person(
            uuid=str(uuid.uuid4()),
            given_name=given_name,
            family_name=family_name,
            full_name_ar=display_name[:300],
            email=email,
            phone=phone,
            is_active=True,
        )
        self.session.add(person)
        await self.session.flush()
        identity = IdentityRecord(
            uuid=str(uuid.uuid4()),
            person_id=person.id,
            identity_type=IdentityType.temporary.value,
            status="active",
            issued_at=self._now(),
            is_active=True,
        )
        self.session.add(identity)
        await self.session.flush()
        account = Account(
            uuid=str(uuid.uuid4()),
            identity_id=identity.id,
            account_type="human",
            status=AccountStatus.approved.value,
            email=email,
            phone=phone,
            password_hash=None,
            is_active=True,
            is_locked=False,
            email_verified=bool(email),
            phone_verified=bool(phone and not email),
            identity_verified=False,
        )
        self.session.add(account)
        await self.session.flush()
        contact_record = VerificationRecord(
            uuid=str(uuid.uuid4()),
            account_id=account.id,
            identity_id=identity.id,
            record_type="contact",
            method=request.verification_method or "contact",
            provider=request.verification_provider or "notification:unknown",
            status=VerificationRecordStatus.not_started.value,
            assurance_level="L0",
            requested_at=request.created_at or self._now(),
            completed_at=request.verified_at,
            valid_from=request.verified_at,
            provider_reference=request.verification_reference,
            verification_session_id=f"contact:{request.request_uuid}",
            verified_by="account_request_otp",
            attributes_purpose="account_request_contact_verification",
            is_active=True,
        )
        self.session.add(contact_record)
        await self.session.flush()
        if request.verified_at:
            VerificationRecordService.transition(contact_record, VerificationRecordStatus.pending)
            VerificationRecordService.transition(contact_record, VerificationRecordStatus.in_progress)
            VerificationRecordService.transition(contact_record, VerificationRecordStatus.verified)
            contact_record.started_at = request.verified_at
            contact_record.completed_at = request.verified_at
            contact_record.valid_from = request.verified_at
            contact_record.assurance_level = "L1"
        request.verification_reference = contact_record.uuid
        request.account_id = account.id
        await self._transition_request(
            request,
            AccountRequestStatus.approved,
            actor_id=actor_id,
            reason_code="account_approved",
            metadata={"account_id": account.id},
        )
        await AuditService(self.session).record(
            AuditAction.account_created,
            actor_id=actor_id,
            actor_type="account",
            target_type="account",
            target_id=account.id,
            metadata={"source": "approved_account_request", "request_id": request.request_uuid},
        )
        await self.session.commit()
        return request, account

    async def issue_activation_token(self, request_uuid: str, actor_id: str) -> bool:
        request = await self._get_request(request_uuid, for_update=True)
        if request is None or request.status != AccountRequestStatus.approved.value or not request.account_id:
            raise AccountRequestStateError("Account is not approved for activation")
        account = await self.session.get(Account, request.account_id)
        if account is None or not account.identity_verified:
            raise AccountRequestStateError("Canonical identity verification is required before activation")
        email = self._decrypt_optional(request.contact_email_encrypted)
        phone = self._decrypt_optional(request.contact_phone_encrypted)
        recipient = email or phone
        if not recipient:
            raise VerificationProviderUnavailable("No activation delivery contact is available")
        token = secrets.token_urlsafe(32)
        # The model field is added by the reversible migration for this command.
        request.activation_token_hash = self._activation_token_hash(token)
        request.activation_token_expires_at = self._now() + _ACTIVATION_TTL
        channel = "email" if email else "sms"
        message = "Use the secure GULA activation link delivered through your approved channel."
        notification = (
            get_service().send_email(recipient, "Activate your GULA account", f"{message} Token: {token}")
            if channel == "email"
            else get_service().send_sms(recipient, f"{message} Token: {token}")
        )
        if not notification.success:
            request.activation_token_hash = None
            request.activation_token_expires_at = None
            raise VerificationProviderUnavailable("Activation provider did not accept the message")
        await self._audit_event(
            event_type="account_activation_token_issued",
            action="account.activation_token_issued",
            request=request,
            actor_id=actor_id,
            decision="allow",
            reason_code="approved_account",
            metadata={"channel": channel},
        )
        await self.session.commit()
        return True

    async def activate(self, request_uuid: str, token: str, password: str) -> Account:
        if len(password) < 12 or len(password) > 128:
            raise AccountRequestStateError("Password does not meet policy")
        request = await self._get_request(request_uuid, for_update=True)
        if request is None or request.status != AccountRequestStatus.approved.value or not request.account_id:
            raise AccountRequestStateError("Account is not ready for activation")
        if not request.activation_token_hash or not request.activation_token_expires_at:
            raise AccountRequestStateError("Activation is not available")
        if request.activation_token_expires_at <= self._now() or not secrets.compare_digest(
            request.activation_token_hash,
            self._activation_token_hash(token),
        ):
            raise AccountRequestStateError("Activation token is invalid or expired")
        account = await self.session.get(Account, request.account_id)
        if account is None:
            raise LookupError("Account not found")
        if not account.identity_verified:
            raise AccountRequestStateError("Canonical identity verification is required before activation")
        try:
            AccountLifecycleService.activate(account)
        except InvalidAccountTransition as exc:
            raise AccountRequestStateError(str(exc)) from exc
        account.password_hash = hash_password(password)
        account.password_changed_at = self._now()
        account.password_expires_at = self._now() + timedelta(days=90)
        account.activated_at = self._now()
        request.activation_token_hash = None
        request.activation_token_expires_at = None
        await AuditService(self.session).record(
            AuditAction.account_activated,
            actor_id=account.id,
            actor_type="account",
            target_type="account",
            target_id=account.id,
            metadata={"source": "activation_token", "request_id": request.request_uuid},
        )
        await self.session.commit()
        return account

    async def mutate_account(
        self,
        account_uuid: str,
        *,
        actor_id: str,
        action: str,
        reason_code: str,
        governance_organization_id: str,
        suspended_until: datetime | None = None,
    ) -> Account:
        account = await self.session.scalar(
            select(Account).where(Account.uuid == account_uuid).with_for_update(),
        )
        if account is None:
            raise LookupError("Account not found")
        membership = await self.session.scalar(
            select(Membership.id).where(
                Membership.account_id == account.id,
                Membership.organization_id == governance_organization_id,
                Membership.status == MembershipStatus.active.value,
                Membership.is_active.is_(True),
            ),
        )
        if membership is None:
            raise AccountRequestStateError("Account is outside the governance organization scope")
        try:
            if action == "suspend":
                AccountLifecycleService.suspend(account, reason_code)
                account.suspended_until = suspended_until
                audit_action = AuditAction.account_suspended
            elif action == "lock":
                AccountLifecycleService.lock(account, reason_code)
                audit_action = AuditAction.account_locked
            elif action == "reactivate":
                AccountLifecycleService.reactivate(account)
                account.suspended_until = None
                audit_action = AuditAction.account_unlocked
            elif action == "deactivate":
                AccountLifecycleService.deactivate(account, reason_code)
                account.suspended_until = None
                account.deactivation_reason = reason_code
                account.deactivated_at = self._now()
                audit_action = AuditAction.account_disabled
            else:
                raise ValueError("Unsupported account action")
        except InvalidAccountTransition as exc:
            raise AccountRequestStateError(str(exc)) from exc
        account.lock_reason = reason_code if action == "lock" else getattr(account, "lock_reason", None)
        await AuditService(self.session).record(
            audit_action,
            actor_id=actor_id,
            actor_type="account",
            target_type="account",
            target_id=account.id,
            organization_id=governance_organization_id,
            metadata={"reason_code": reason_code, "action": action},
        )
        await self.session.commit()
        return account

    async def expire(self, request_uuid: str, actor_id: str | None = None) -> AccountCreationRequest:
        request = await self._get_request(request_uuid, for_update=True)
        if request is None:
            raise LookupError("Account request not found")
        await self._transition_request(
            request,
            AccountRequestStatus.expired,
            actor_id=actor_id,
            reason_code="request_expired",
        )
        await self.session.commit()
        return request

    @staticmethod
    def public_result(account_request: AccountCreationRequest | None) -> dict[str, Any]:
        return {
            "accepted": True,
            "status": account_request.status if account_request else AccountRequestStatus.pending_review.value,
            "request_id": account_request.request_uuid if account_request else None,
            "message": "Your request was received for review.",
        }

    @staticmethod
    def serialize_request(account_request: AccountCreationRequest) -> dict[str, Any]:
        return {
            "request_id": account_request.request_uuid,
            "status": account_request.status,
            "requested_account_type": account_request.requested_account_type,
            "account_id": account_request.account_id,
            "reviewed_at": account_request.reviewed_at.isoformat() if account_request.reviewed_at else None,
            "verified_at": account_request.verified_at.isoformat() if account_request.verified_at else None,
            "expires_at": account_request.expires_at.isoformat() if account_request.expires_at else None,
            "is_active": account_request.is_active,
        }

    @staticmethod
    def serialize_account(account: Account) -> dict[str, Any]:
        return {
            "account_id": account.id,
            "account_uuid": account.uuid,
            "identity_id": account.identity_id,
            "status": account.status,
            "is_active": account.is_active,
            "is_locked": account.is_locked,
            "suspended_until": account.suspended_until.isoformat() if account.suspended_until else None,
            "email_verified": account.email_verified,
            "phone_verified": account.phone_verified,
            "identity_verified": account.identity_verified,
            "activated_at": account.activated_at.isoformat() if account.activated_at else None,
        }
