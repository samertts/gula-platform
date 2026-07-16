from __future__ import annotations


class BiomedicalException(Exception):
    pass


class DeviceNotFoundError(BiomedicalException):
    pass


class WorkOrderNotFoundError(BiomedicalException):
    pass


class TechnicianNotFoundError(BiomedicalException):
    pass


class VendorNotFoundError(BiomedicalException):
    pass


class AssetNotFoundError(BiomedicalException):
    pass


class CalibrationNotFoundError(BiomedicalException):
    pass


class MaintenanceNotFoundError(BiomedicalException):
    pass


class SparePartNotFoundError(BiomedicalException):
    pass


class ContractNotFoundError(BiomedicalException):
    pass


class DeviceRecallNotFoundError(BiomedicalException):
    pass


class DeviceIncidentNotFoundError(BiomedicalException):
    pass


class InventoryNotFoundError(BiomedicalException):
    pass
