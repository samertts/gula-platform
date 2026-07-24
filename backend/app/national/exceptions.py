from __future__ import annotations


class NationalDomainError(Exception):
    pass


class CitizenNotFoundError(NationalDomainError):
    def __init__(self, citizen_id: str) -> None:
        self.citizen_id = citizen_id
        super().__init__(f"Citizen not found: {citizen_id}")


class PatientNotFoundError(NationalDomainError):
    def __init__(self, patient_id: str) -> None:
        self.patient_id = patient_id
        super().__init__(f"Patient not found: {patient_id}")


class DuplicateCitizenError(NationalDomainError):
    def __init__(self, national_id: str) -> None:
        self.national_id = national_id
        super().__init__(f"Duplicate citizen for national ID: {national_id}")


class DuplicateHealthNumberError(NationalDomainError):
    def __init__(self, health_number: str) -> None:
        self.health_number = health_number
        super().__init__(f"Duplicate health number: {health_number}")


class IdentityMergeError(NationalDomainError):
    def __init__(self, primary_id: str, secondary_id: str, reason: str) -> None:
        self.primary_id = primary_id
        self.secondary_id = secondary_id
        self.reason = reason
        super().__init__(f"Identity merge failed: {primary_id} <- {secondary_id}: {reason}")


class InvalidStateTransitionError(NationalDomainError):
    def __init__(self, entity: str, current: str, target: str) -> None:
        self.entity = entity
        self.current = current
        self.target = target
        super().__init__(f"Invalid state transition: {entity} from {current} to {target}")


class WorkflowExecutionError(NationalDomainError):
    def __init__(self, workflow: str, step: str, reason: str) -> None:
        self.workflow = workflow
        self.step = step
        self.reason = reason
        super().__init__(f"Workflow {workflow} failed at step {step}: {reason}")


class ConsentNotGrantedError(NationalDomainError):
    def __init__(self, patient_id: str, scope: str) -> None:
        self.patient_id = patient_id
        self.scope = scope
        super().__init__(f"Consent not granted for patient {patient_id} scope {scope}")


class BreakGlassRequiredError(NationalDomainError):
    def __init__(self, resource: str, reason: str) -> None:
        self.resource = resource
        self.reason = reason
        super().__init__(f"Break glass required for {resource}: {reason}")


class AccessDeniedError(NationalDomainError):
    def __init__(self, user_id: str, resource: str, permission: str) -> None:
        self.user_id = user_id
        self.resource = resource
        self.permission = permission
        super().__init__(f"Access denied: user {user_id} needs {permission} on {resource}")


class FHIRValidationError(NationalDomainError):
    def __init__(self, resource_type: str, errors: list[str]) -> None:
        self.resource_type = resource_type
        self.errors = errors
        super().__init__(f"FHIR validation failed for {resource_type}: {'; '.join(errors)}")


class ReferenceDataNotFoundError(NationalDomainError):
    def __init__(self, ref_type: str, code: str) -> None:
        self.ref_type = ref_type
        self.code = code
        super().__init__(f"Reference data not found: {ref_type} code {code}")


class GuardianNotFoundError(NationalDomainError):
    def __init__(self, guardian_id: str) -> None:
        self.guardian_id = guardian_id
        super().__init__(f"Guardian not found: {guardian_id}")


class FamilyNotFoundError(NationalDomainError):
    def __init__(self, family_id: str) -> None:
        self.family_id = family_id
        super().__init__(f"Family not found: {family_id}")


class EncounterNotFoundError(NationalDomainError):
    def __init__(self, encounter_id: str) -> None:
        self.encounter_id = encounter_id
        super().__init__(f"Encounter not found: {encounter_id}")


class ReferralNotFoundError(NationalDomainError):
    def __init__(self, referral_id: str) -> None:
        self.referral_id = referral_id
        super().__init__(f"Referral not found: {referral_id}")


class InvalidNationalIdError(NationalDomainError):
    def __init__(self, national_id: str, reason: str) -> None:
        self.national_id = national_id
        self.reason = reason
        super().__init__(f"Invalid national ID {national_id}: {reason}")


class NewbornRegistrationError(NationalDomainError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Newborn registration failed: {reason}")


class ForeignerRegistrationError(NationalDomainError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Foreigner registration failed: {reason}")


class OfflineSyncConflictError(NationalDomainError):
    def __init__(self, entity: str, entity_id: str, local_version: int, remote_version: int) -> None:
        self.entity = entity
        self.entity_id = entity_id
        self.local_version = local_version
        self.remote_version = remote_version
        super().__init__(
            f"Offline sync conflict: {entity} {entity_id} "
            f"local v{local_version} != remote v{remote_version}",
        )


class OptimisticLockError(NationalDomainError):
    def __init__(self, entity: str, entity_id: str, expected_version: int) -> None:
        self.entity = entity
        self.entity_id = entity_id
        self.expected_version = expected_version
        super().__init__(f"Optimistic lock failed: {entity} {entity_id} expected version {expected_version}")
