from __future__ import annotations

import logging
from pathlib import Path

from ..domain.entities import DocumentPage
from ..domain.enums import OcrEngine, OcrLanguage
from .base import OcrProviderBase

logger = logging.getLogger("gula.document_intelligence.providers.paddle")


class PaddleOcrProvider(OcrProviderBase):
    def __init__(self) -> None:
        super().__init__()
        self._ocr = None
        self._numpy = None

    @property
    def engine_type(self) -> OcrEngine:
        return OcrEngine.paddle_ocr

    @property
    def display_name(self) -> str:
        return "PaddleOCR"

    @property
    def requires_gpu(self) -> bool:
        return False

    @property
    def version(self) -> str:
        try:
            import paddleocr

            return paddleocr.__version__
        except Exception:
            return "unknown"

    async def initialize(self) -> None:
        try:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="ar",
                use_gpu=False,
                show_log=False,
            )
            self._initialized = True
            logger.info("PaddleOCR initialized (version: %s)", self.version)
        except ImportError:
            logger.warning("paddleocr not installed — PaddleOCR provider unavailable")
        except Exception as exc:
            logger.warning("PaddleOCR initialization failed: %s", exc)

    async def shutdown(self) -> None:
        self._ocr = None
        self._initialized = False
        logger.info("PaddleOCR shut down")

    async def get_supported_languages(self) -> list[OcrLanguage]:
        return [
            OcrLanguage.arabic,
            OcrLanguage.english,
            OcrLanguage.arabic_english,
        ]

    async def ocr_image(
        self,
        image_data: bytes,
        language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> DocumentPage:
        if not self._initialized:
            await self.initialize()
        if not self._ocr:
            return DocumentPage(text="", confidence=0.0, ocr_engine=self.engine_type)

        page = DocumentPage(ocr_engine=self.engine_type, language=language)

        try:
            import tempfile

            with tempfile.TemporaryDirectory(prefix="gula-paddleocr-") as temp_dir:
                tmp_path = Path(temp_dir) / "image.png"
                tmp_path.write_bytes(image_data)
                result = self._ocr.ocr(str(tmp_path), cls=True)
                text_parts = []
                confidences = []
                for line_group in result or []:
                    for line in line_group or []:
                        if len(line) >= 2:
                            text, confidence = line[1][0], line[1][1]
                            text_parts.append(str(text))
                            confidences.append(float(confidence))

                page.text = " ".join(text_parts)
                page.confidence = sum(confidences) / len(confidences) if confidences else 0.0

        except Exception as exc:
            logger.error("PaddleOCR failed: %s", exc)
            page.text = ""
            page.confidence = 0.0

        return page

    async def ocr_image_path(
        self,
        image_path: Path,
        language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> DocumentPage:
        return await self.ocr_image(image_path.read_bytes(), language)
