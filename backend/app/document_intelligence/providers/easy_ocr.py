from __future__ import annotations

import logging
from pathlib import Path

from ..domain.entities import DocumentPage
from ..domain.enums import OcrEngine, OcrLanguage
from .base import OcrProviderBase

logger = logging.getLogger("gula.document_intelligence.providers.easyocr")


class EasyOcrProvider(OcrProviderBase):
    def __init__(self) -> None:
        super().__init__()
        self._reader = None

    @property
    def engine_type(self) -> OcrEngine:
        return OcrEngine.easy_ocr

    @property
    def display_name(self) -> str:
        return "EasyOCR"

    @property
    def requires_gpu(self) -> bool:
        return False

    @property
    def version(self) -> str:
        try:
            import easyocr
            return easyocr.__version__
        except Exception:
            return "unknown"

    async def initialize(self) -> None:
        try:
            import easyocr
            self._reader = easyocr.Reader(
                ["ar", "en"],
                gpu=False,
                verbose=False,
            )
            self._initialized = True
            logger.info("EasyOCR initialized (version: %s)", self.version)
        except ImportError:
            logger.warning("easyocr not installed — EasyOCR provider unavailable")
        except Exception as exc:
            logger.warning("EasyOCR initialization failed: %s", exc)

    async def shutdown(self) -> None:
        self._reader = None
        self._initialized = False
        logger.info("EasyOCR shut down")

    async def get_supported_languages(self) -> list[OcrLanguage]:
        return [
            OcrLanguage.arabic,
            OcrLanguage.english,
            OcrLanguage.arabic_english,
        ]

    async def ocr_image(
        self, image_data: bytes, language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> DocumentPage:
        if not self._initialized:
            await self.initialize()
        if not self._reader:
            return DocumentPage(text="", confidence=0.0, ocr_engine=self.engine_type)

        page = DocumentPage(ocr_engine=self.engine_type, language=language)

        try:
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_data)
                tmp_path = tmp.name

            try:
                result = self._reader.readtext(tmp_path)
                text_parts = []
                confidences = []
                for _bbox, text, confidence in result:
                    text_parts.append(str(text))
                    confidences.append(float(confidence))

                page.text = " ".join(text_parts)
                page.confidence = (
                    sum(confidences) / len(confidences) if confidences else 0.0
                )
            finally:
                import os
                os.unlink(tmp_path)

        except Exception as exc:
            logger.error("EasyOCR failed: %s", exc)
            page.text = ""
            page.confidence = 0.0

        return page

    async def ocr_image_path(
        self, image_path: Path, language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> DocumentPage:
        return await self.ocr_image(image_path.read_bytes(), language)
