"""National LIMS Analyzer Integration Platform.

Universal protocol support for lab instrument communication:
  - ASTM (E1394, E1381)
  - HL7 v2.x
  - FHIR R4
  - REST APIs
  - TCP/IP, Serial, USB

Each protocol implements the AnalyzerProtocol interface.
"""

from . import astm
from . import hl7
from . import device_registry
from . import simulator

__all__ = ["astm", "hl7", "device_registry", "simulator"]
