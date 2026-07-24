"""National ID card scanning endpoint.

Provides camera-based capture and OCR extraction of Iraqi National ID card fields:
- National ID number (12 digits)
- Full name
- Date of birth

Uses OpenCV for image preprocessing and Tesseract for OCR.
Falls back to regex-based extraction if OCR libraries are not available.
"""

import asyncio
import io
import re

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user
from ..security.rate_limit import rate_limit_auth
from ..services.identity import hash_national_id

router = APIRouter(prefix="/id-scan", tags=["identity"])


# Iraqi National ID patterns
NATIONAL_ID_PATTERN = re.compile(r"\b\d{12,13}\b")
DATE_PATTERN = re.compile(r"\b(\d{4})[/\-.](\d{2})[/\-.](\d{2})\b")


def preprocess_image(image_bytes: bytes):
    """Preprocess image for better OCR accuracy.

    Applies: grayscale, adaptive threshold, noise removal.
    Returns processed image or None if OpenCV not available.
    """
    try:
        import cv2
        import numpy as np

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply adaptive threshold for better text contrast
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2,
        )

        # Denoise
        return cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

    except ImportError:
        return None


def extract_text_ocr(image_bytes: bytes) -> str:
    """Extract text from image using Tesseract OCR.

    Tries both Arabic and English language packs.
    """
    try:
        import pytesseract
        from PIL import Image

        # Try preprocessed image first
        processed = preprocess_image(image_bytes)

        if processed is not None:
            # Convert OpenCV image to PIL
            pil_img = Image.fromarray(processed)
        else:
            pil_img = Image.open(io.BytesIO(image_bytes))

        # Extract with both Arabic and English
        return pytesseract.image_to_string(pil_img, lang="ara+eng")

    except ImportError:
        return ""
    except Exception:
        return ""


def extract_fields(text: str) -> dict:
    """Extract structured fields from OCR text."""
    result = {
        "national_id": None,
        "name": None,
        "birth_date": None,
        "raw_text": text[:500] if text else None,
    }

    if not text:
        return result

    # Extract national ID (12-13 digit number)
    id_match = NATIONAL_ID_PATTERN.search(text)
    if id_match:
        result["national_id"] = id_match.group()

    # Extract dates with validation
    dates = DATE_PATTERN.findall(text)
    if dates:
        year, month, day = dates[-1]
        try:
            y, m, d = int(year), int(month), int(day)
            if 1900 <= y <= 2025 and 1 <= m <= 12 and 1 <= d <= 31:
                result["birth_date"] = f"{year}-{month}-{day}"
        except ValueError:
            pass

    # Try to extract name (lines that contain mostly letters)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    name_candidates = []
    for line in lines:
        # Skip lines that are mostly numbers or very short
        if len(line) < 3:
            continue
        letter_ratio = sum(1 for c in line if c.isalpha() or c == " ") / max(len(line), 1)
        if letter_ratio > 0.7 and len(line) > 4:
            name_candidates.append(line)

    if name_candidates:
        # Take the longest candidate as the name
        result["name"] = max(name_candidates, key=len)

    return result


@router.post("/scan")
async def scan_national_id(
    image: UploadFile = File(...),
    request: Request = None,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Scan a national ID card image and extract fields.

    Upload a photo of an Iraqi National ID card.
    The system will extract: national ID number, name, and date of birth.

    The user should confirm the extracted data before it's used.
    The image is NOT stored - only extracted text fields are returned.
    """
    # Rate limit OCR requests (CPU-intensive operation)
    if request:
        rate_limit_auth(request, max_per_minute=5)

    # Validate content type strictly
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
    if not image.content_type or image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, detail="Please upload a valid image file (JPEG, PNG, WebP, BMP)",
        )

    # Read image (max 2MB - ID card photos shouldn't be larger)
    contents = await image.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large (max 2MB)")
    if len(contents) < 1000:
        raise HTTPException(status_code=400, detail="Image too small - may be corrupted")

    # Extract text via OCR (CPU-intensive - run in executor to avoid blocking event loop)
    def _run_ocr():
        text = extract_text_ocr(contents)
        fields = extract_fields(text)
        nid_hash = None
        if fields["national_id"]:
            nid_hash = hash_national_id(fields["national_id"])
        return fields, nid_hash

    loop = asyncio.get_event_loop()
    fields, nid_hash = await loop.run_in_executor(None, _run_ocr)

    return {
        "success": bool(fields["national_id"] or fields["name"]),
        "fields": {
            "national_id": fields["national_id"],
            "national_id_hash": nid_hash,
            "name": fields["name"],
            "birth_date": fields["birth_date"],
        },
        "needs_confirmation": True,
        "message": "Please verify the extracted data before confirming.",
        "message_ar": "يرجى التحقق من البيانات المستخرجة قبل التأكيد.",
    }
