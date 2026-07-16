from __future__ import annotations


class BloodBankException(Exception):
    pass


class DonorNotFoundError(BloodBankException):
    pass


class DonationNotFoundError(BloodBankException):
    pass


class DonorDeferredError(BloodBankException):
    pass


class BloodInventoryNotFoundError(BloodBankException):
    pass


class InsufficientStockError(BloodBankException):
    pass


class CrossmatchNotFoundError(BloodBankException):
    pass


class CrossmatchConflictError(BloodBankException):
    pass


class TransfusionNotFoundError(BloodBankException):
    pass


class TransfusionReactionError(BloodBankException):
    pass


class ComponentProcessingError(BloodBankException):
    pass


class ColdChainViolationError(BloodBankException):
    pass


class DonorEligibilityError(BloodBankException):
    pass


class BagIdentifierError(BloodBankException):
    pass


class ExpiredUnitError(BloodBankException):
    pass


class RecallNotFoundError(BloodBankException):
    pass
