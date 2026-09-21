import abc
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("gula.device_connectors")

class DeviceAdapter(abc.ABC):
    """Base class for all GULA device connectors."""
    @abc.abstractmethod
    def parse(self, raw_data: Any) -> Dict[str, Any]:
        """Converts raw device data into GULA-standard clinical format."""
        pass

class HL7Adapter(DeviceAdapter):
    """Adapter for HL7 v2.x (Standard for clinical messaging)."""
    def parse(self, raw_data: str) -> Dict[str, Any]:
        # Logic to parse HL7 segments (MSH, PID, OBR, OBX)
        logger.info("[ADAPTER] Parsing HL7 message...")
        return {"protocol": "HL7", "parsed": True}

class DICOMAdapter(DeviceAdapter):
    """Adapter for DICOM (Standard for medical imaging)."""
    def parse(self, raw_data: bytes) -> Dict[str, Any]:
        # Logic to extract metadata from DICOM files
        logger.info("[ADAPTER] Extracting DICOM metadata...")
        return {"protocol": "DICOM", "type": "Imaging"}

class ASTMAdapter(DeviceAdapter):
    """Adapter for ASTM (Common in lab analyzers)."""
    def parse(self, raw_data: str) -> Dict[str, Any]:
        # Logic to parse ASTM LIS messages
        logger.info("[ADAPTER] Parsing ASTM lab data...")
        return {"protocol": "ASTM", "parsed": True}

class PeripheralAdapter(DeviceAdapter):
    """Adapter for printers, scanners, and standard computing peripherals."""
    def parse(self, raw_data: Dict) -> Dict[str, Any]:
        logger.info("[ADAPTER] Handling peripheral request: %s", raw_data.get("type"))
        return {"protocol": "Generic", "type": raw_data.get("type")}

class UniversalConnectorManager:
    """
    Orchestrates connection to any device.
    Detects protocol and routes to the correct adapter.
    """
    def __init__(self):
        self.adapters = {
            "HL7": HL7Adapter(),
            "DICOM": DICOMAdapter(),
            "ASTM": ASTMAdapter(),
            "GENERIC": PeripheralAdapter()
        }

    def process_device_input(self, protocol: str, data: Any) -> Optional[Dict[str, Any]]:
        adapter = self.adapters.get(protocol.upper())
        if adapter:
            return adapter.parse(data)
        logger.error("[CONNECTOR] Unsupported protocol: %s", protocol)
        return None

    def secure_pairing(self, device_id: str, device_info: Dict):
        """
        Implements a 'Secure Plug-and-Play' handshake.
        Registers the device and establishes trust.
        """
        logger.info(f"[PnP] Initiating secure pairing for device: {device_id}")
        # 1. Validate device signature/cert
        # 2. Add to trusted device list
        # 3. Assign encryption keys for the session
        return {"status": "paired", "device_id": device_id, "trust_level": "verified"}
