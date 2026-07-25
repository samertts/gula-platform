from __future__ import annotations

import base64
import logging
import time
from typing import Any

from backend.app.integration.connectors import BaseConnector, ConnectorRegistry

logger = logging.getLogger("gula.integration.connectors.barcode")

SUPPORTED_BARCODE_FORMATS = frozenset(
    {"code128", "ean13", "ean8", "upca", "upce", "code39", "qrcode"}
)


class BarcodeConnector(BaseConnector):
    def __init__(
        self,
        name: str = "barcode",
        version: str = "1.0.0",
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name, version, config)
        self._default_format = self.config.get("default_format", "qrcode")
        self._default_width = self.config.get("width", 300)
        self._default_height = self.config.get("height", 300)
        self._barcode_backend = self.config.get("backend", "python-barcode")

    async def connect(self) -> bool:
        try:
            self._connected = True
            logger.info("Barcode connector ready: backend=%s", self._barcode_backend)
            return True
        except Exception as exc:
            logger.error("Barcode connector failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        self._connected = False
        logger.info("Barcode connector disconnected")
        return True

    async def health_check(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "connected": self._connected,
            "timestamp": time.time(),
            "status": "healthy" if self._connected else "disconnected",
            "backend": self._barcode_backend,
        }

    async def send(self, data: dict[str, Any]) -> dict[str, Any]:
        action = data.get("action", "generate")
        if action == "generate":
            return await self._generate(data)
        if action == "scan":
            return await self._scan(data)
        raise ValueError(f"Unknown barcode action: {action}")

    async def _generate(self, data: dict[str, Any]) -> dict[str, Any]:
        payload = data.get("data", "")
        format_type = data.get("format", self._default_format)
        width = data.get("width", self._default_width)
        height = data.get("height", self._default_height)
        if not payload:
            return {"success": False, "error": "data required for barcode generation"}
        if format_type not in SUPPORTED_BARCODE_FORMATS:
            return {
                "success": False,
                "error": f"Unsupported format: {format_type}. Supported: {', '.join(sorted(SUPPORTED_BARCODE_FORMATS))}",
            }

        try:
            if format_type == "qrcode":
                return await self._generate_qr(payload, width, height)
            return await self._generate_barcode(payload, format_type, width, height)
        except Exception as exc:
            logger.error("Barcode generation failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def _generate_qr(self, payload: str, width: int, height: int) -> dict[str, Any]:
        try:
            from io import BytesIO

            import qrcode

            qr = qrcode.QRCode(
                version=self.config.get("qr_version", 1),
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=self.config.get("qr_box_size", 10),
                border=self.config.get("qr_border", 4),
            )
            qr.add_data(payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((width, height))

            buf = BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")

            return {
                "success": True,
                "format": "qrcode",
                "data_uri": f"data:image/png;base64,{b64}",
                "width": width,
                "height": height,
            }
        except ImportError:
            logger.warning("qrcode library not installed, returning text representation")
            return {
                "success": True,
                "format": "qrcode_text",
                "data": payload,
                "note": "qrcode library not available",
            }

    async def _generate_barcode(
        self, payload: str, format_type: str, width: int, height: int
    ) -> dict[str, Any]:
        try:
            from io import BytesIO

            import barcode
            from barcode.writer import ImageWriter

            format_map = {
                "code128": "code128",
                "ean13": "ean13",
                "ean8": "ean8",
                "upca": "upc-a",
                "upce": "upc-e",
                "code39": "code39",
            }
            barcode_format = format_map.get(format_type, format_type)
            writer = ImageWriter()
            writer.set_options({"module_width": 0.2, "module_height": height / 100})
            rv = barcode.get(barcode_format, payload, writer=writer)

            buf = BytesIO()
            rv.write(buf)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")

            return {
                "success": True,
                "format": format_type,
                "data_uri": f"data:image/png;base64,{b64}",
                "width": width,
                "height": height,
            }
        except ImportError:
            logger.warning("python-barcode library not installed")
            return {
                "success": True,
                "format": f"{format_type}_text",
                "data": payload,
                "note": "python-barcode library not available",
            }

    async def _scan(self, data: dict[str, Any]) -> dict[str, Any]:
        image_data = data.get("image", "")
        if not image_data:
            return {"success": False, "error": "image data required for scanning"}
        try:
            from io import BytesIO

            from PIL import Image
            from pyzbar import pyzbar

            if image_data.startswith("data:image"):
                b64_data = image_data.split(",")[1]
            else:
                b64_data = image_data
            image_bytes = base64.b64decode(b64_data)
            image = Image.open(BytesIO(image_bytes))
            decoded = pyzbar.decode(image)
            results = []
            for obj in decoded:
                results.append(
                    {
                        "data": obj.data.decode("utf-8"),
                        "type": obj.type,
                        "rect": {
                            "left": obj.rect.left,
                            "top": obj.rect.top,
                            "width": obj.rect.width,
                            "height": obj.rect.height,
                        },
                    }
                )
            return {"success": True, "results": results, "count": len(results)}
        except ImportError:
            logger.warning("pyzbar or PIL not installed, returning placeholder")
            return {
                "success": True,
                "note": "barcode scanning libraries not available",
                "results": [],
            }
        except Exception as exc:
            logger.error("Barcode scanning failed: %s", exc)
            return {"success": False, "error": str(exc)}


ConnectorRegistry.register("barcode", BarcodeConnector)
