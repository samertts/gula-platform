from .base import OcrProviderBase
from .easy_ocr import EasyOcrProvider
from .manager import OcrProviderManager
from .paddle_ocr import PaddleOcrProvider
from .tesseract import TesseractProvider

__all__ = [
    "OcrProviderBase",
    "OcrProviderManager",
    "TesseractProvider",
    "PaddleOcrProvider",
    "EasyOcrProvider",
]
