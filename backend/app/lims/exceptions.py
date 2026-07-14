"""National LIMS custom exceptions."""


class LIMSError(Exception):
    """Base exception for National LIMS."""


class SpecimenStateError(LIMSError):
    """Invalid specimen state transition."""


class OrderStateError(LIMSError):
    """Invalid order state transition."""


class InstrumentOffline(LIMSError):
    """Instrument is offline or not reachable."""


class QCError(LIMSError):
    """Quality control failure."""


class ValidationError(LIMSError):
    """Result validation failure."""


class DeltaCheckFailed(LIMSError):
    """Delta check threshold exceeded."""


class ReferenceRangeNotFound(LIMSError):
    """No matching reference range found."""


class CriticalValueError(LIMSError):
    """Critical value detected — requires immediate attention."""


class InventoryShortage(LIMSError):
    """Insufficient reagent/consumable inventory."""


class LotExpired(LIMSError):
    """Lot has expired."""


class ElectronicSignatureRequired(LIMSError):
    """Electronic signature required for this operation."""


class ReportGenerationError(LIMSError):
    """Error generating laboratory report."""


class AnalyzerCommunicationError(LIMSError):
    """Error communicating with analyzer."""


class DuplicateSpecimenBarcode(LIMSError):
    """Specimen barcode already exists."""


class AccessionNumberConflict(LIMSError):
    """Accession number already in use."""


class SpecimenRejected(LIMSError):
    """Specimen has been rejected — cannot proceed."""
