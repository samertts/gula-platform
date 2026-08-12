from __future__ import annotations


class EMSException(Exception):
    pass


class IncidentNotFoundError(EMSException):
    pass


class DispatchNotFoundError(EMSException):
    pass


class AmbulanceNotFoundError(EMSException):
    pass


class AmbulanceNotAvailableError(EMSException):
    pass


class CrewNotFoundError(EMSException):
    pass


class CrewNotAvailableError(EMSException):
    pass


class InvalidIncidentStateError(EMSException):
    pass


class TriageNotFoundError(EMSException):
    pass


class DisasterEventNotFoundError(EMSException):
    pass


class ShelterNotFoundError(EMSException):
    pass


class MassCasualtyIncidentNotFoundError(EMSException):
    pass


class ePCRNotFoundError(EMSException):
    pass


class ResourceAllocationError(EMSException):
    pass
