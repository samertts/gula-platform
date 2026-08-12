from __future__ import annotations

import logging
from pathlib import Path

from ..domain.entities import DocumentPage
from ..domain.enums import OcrEngine, OcrLanguage
from .base import OcrProviderBase

logger = logging.getLogger("gula.document_intelligence.providers.tesseract")


class TesseractProvider(OcrProviderBase):
    def __init__(self) -> None:
        super().__init__()
        self._tesseract_available = False
        self._pytesseract = None
        self._cv2 = None
        self._numpy = None

    @property
    def engine_type(self) -> OcrEngine:
        return OcrEngine.tesseract

    @property
    def display_name(self) -> str:
        return "Tesseract OCR"

    @property
    def requires_gpu(self) -> bool:
        return False

    @property
    def version(self) -> str:
        try:
            import pytesseract
            return pytesseract.get_tesseract_version()
        except Exception:
            return "unknown"

    async def initialize(self) -> None:
        try:
            import pytesseract
            self._pytesseract = pytesseract
            self._tesseract_available = True
            logger.info("Tesseract OCR initialized (version: %s)", self.version)
        except ImportError:
            logger.warning("pytesseract not installed — Tesseract provider unavailable")
            self._tesseract_available = False
            return

        try:
            import cv2
            self._cv2 = cv2
        except ImportError:
            logger.warning("opencv-python not installed — image preprocessing disabled")

        try:
            import numpy
            self._numpy = numpy
        except ImportError:
            pass

        self._initialized = True

    async def shutdown(self) -> None:
        self._initialized = False
        logger.info("Tesseract OCR shut down")

    async def get_supported_languages(self) -> list[OcrLanguage]:
        return [
            OcrLanguage.arabic,
            OcrLanguage.english,
            OcrLanguage.arabic_english,
            OcrLanguage.kurdish,
        ]

    async def ocr_image(
        self, image_data: bytes, language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> DocumentPage:
        if not self._initialized:
            await self.initialize()
        if not self._tesseract_available:
            return DocumentPage(text="", confidence=0.0, ocr_engine=self.engine_type)

        lang_map = {
            OcrLanguage.arabic: "ara",
            OcrLanguage.english: "eng",
            OcrLanguage.arabic_english: "ara+eng",
            OcrLanguage.kurdish: "kur",
            OcrLanguage.arabic_english_kurdish: "ara+eng+kur",
            OcrLanguage.auto: "ara+eng",
        }
        tesseract_lang = lang_map.get(language, "ara+eng")

        page = DocumentPage(ocr_engine=self.engine_type, language=language)

        try:
            if self._cv2 and self._numpy:
                np_arr = self._numpy.frombuffer(image_data, self._numpy.uint8)
                img = self._cv2.imdecode(np_arr, self._cv2.IMREAD_COLOR)
                if img is not None:
                    page.height, page.width = img.shape[:2]
                    gray = self._cv2.cvtColor(img, self._cv2.COLOR_BGR2GRAY)
                    _, encoded = self._cv2.imencode(".png", gray)
                    processed_bytes = encoded.tobytes()
                else:
                    processed_bytes = image_data
            else:
                processed_bytes = image_data

            data = self._pytesseract.image_to_data(
                processed_bytes,
                lang=tesseract_lang,
                output_type=self._pytesseract.Output.DICT,
                config="--psm 6 --oem 3",
            )

            text_parts = []
            confidences = []
            for i, text in enumerate(data.get("text", [])):
                if text and text.strip():
                    text_parts.append(text.strip())
                    conf = int(data.get("conf", [0])[i])
                    if conf > 0:
                        confidences.append(conf / 100.0)

            page.text = " ".join(text_parts)
            page.confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )

        except Exception as exc:
            logger.error("Tesseract OCR failed: %s", exc)
            page.text = ""
            page.confidence = 0.0

        return page

    async def ocr_image_path(
        self, image_path: Path, language: OcrLanguage = OcrLanguage.arabic_english,
    ) -> DocumentPage:
        data = image_path.read_bytes()
        return await self.ocr_image(data, language)
