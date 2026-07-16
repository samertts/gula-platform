"""National LIMS Analyzer Integration Platform.

Universal protocol support for lab instrument communication:
  - ASTM (E1394, E1381)
  - HL7 v2.x
  - FHIR R4
  - REST APIs
  - TCP/IP, Serial, USB

Each protocol implements the AnalyzerProtocol interface.
"""

from . import astm, device_registry, hl7, simulator

__all__ = ["astm", "device_registry", "hl7", "simulator"]
