from pathlib import Path

import pytest
from app.document_intelligence.domain.enums import OcrLanguage
from app.document_intelligence.providers.easy_ocr import EasyOcrProvider
from app.document_intelligence.providers.paddle_ocr import PaddleOcrProvider


class _FakeEasyReader:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def readtext(self, path: str) -> list[tuple[list[object], str, float]]:
        image_path = Path(path)
        self.paths.append(image_path)
        assert image_path.read_bytes() == b"synthetic-image"
        return [([], "synthetic", 0.9)]


class _FakePaddleReader:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def ocr(self, path: str, *, cls: bool) -> list[list[tuple[list[object], list[object]]]]:
        assert cls is True
        image_path = Path(path)
        self.paths.append(image_path)
        assert image_path.read_bytes() == b"synthetic-image"
        return [[([], ["synthetic", 0.8])]]


@pytest.mark.asyncio
async def test_easyocr_uses_ephemeral_directory_and_cleans_it() -> None:
    provider = EasyOcrProvider()
    provider._initialized = True
    reader = _FakeEasyReader()
    provider._reader = reader

    page = await provider.ocr_image(b"synthetic-image", OcrLanguage.arabic_english)

    assert page.text == "synthetic"
    assert page.confidence == pytest.approx(0.9)
    assert len(reader.paths) == 1
    assert not reader.paths[0].exists()
    assert not reader.paths[0].parent.exists()


@pytest.mark.asyncio
async def test_paddleocr_uses_ephemeral_directory_and_cleans_it() -> None:
    provider = PaddleOcrProvider()
    provider._initialized = True
    reader = _FakePaddleReader()
    provider._ocr = reader

    page = await provider.ocr_image(b"synthetic-image", OcrLanguage.arabic_english)

    assert page.text == "synthetic"
    assert page.confidence == pytest.approx(0.8)
    assert len(reader.paths) == 1
    assert not reader.paths[0].exists()
    assert not reader.paths[0].parent.exists()
