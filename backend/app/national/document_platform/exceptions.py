from __future__ import annotations

from app.national.exceptions import NationalDomainError


class DocumentNotFoundError(NationalDomainError):
    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")


class DocumentValidationError(NationalDomainError):
    def __init__(self, document_id: str, reason: str) -> None:
        self.document_id = document_id
        self.reason = reason
        super().__init__(f"Document validation failed: {document_id}: {reason}")


class DocumentVersionNotFoundError(NationalDomainError):
    def __init__(self, version_id: str) -> None:
        self.version_id = version_id
        super().__init__(f"Document version not found: {version_id}")


class SignatureNotFoundError(NationalDomainError):
    def __init__(self, signature_id: str) -> None:
        self.signature_id = signature_id
        super().__init__(f"Electronic signature not found: {signature_id}")


class SignatureVerificationError(NationalDomainError):
    def __init__(self, signature_id: str, reason: str) -> None:
        self.signature_id = signature_id
        self.reason = reason
        super().__init__(f"Signature verification failed: {signature_id}: {reason}")


class QRCodeNotFoundError(NationalDomainError):
    def __init__(self, qr_code_id: str) -> None:
        self.qr_code_id = qr_code_id
        super().__init__(f"QR code not found: {qr_code_id}")


class AttachmentNotFoundError(NationalDomainError):
    def __init__(self, attachment_id: str) -> None:
        self.attachment_id = attachment_id
        super().__init__(f"Attachment not found: {attachment_id}")


class RetentionRuleNotFoundError(NationalDomainError):
    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id
        super().__init__(f"Retention rule not found: {rule_id}")


class DocumentStateTransitionError(NationalDomainError):
    def __init__(self, document_id: str, current_status: str, target_status: str) -> None:
        self.document_id = document_id
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid state transition for document {document_id}: {current_status} -> {target_status}",
        )


class HashMismatchError(NationalDomainError):
    def __init__(self, document_id: str, expected: str, actual: str) -> None:
        self.document_id = document_id
        self.expected = expected
        self.actual = actual
        super().__init__(f"Hash mismatch for document {document_id}: expected {expected}, got {actual}")


class StorageError(NationalDomainError):
    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(f"Storage error at {path}: {reason}")
