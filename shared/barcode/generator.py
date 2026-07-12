from __future__ import annotations

import io
import logging
import secrets
import string

logger = logging.getLogger("gula.barcode")


def generate_barcode(length: int = 12) -> str:
    chars = string.ascii_uppercase + string.digits
    return "G" + "".join(secrets.choice(chars) for _ in range(length - 1))


def generate_sample_barcode(prefix: str = "SMP") -> str:
    chars = string.ascii_uppercase + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(9))
    return f"{prefix}-{random_part}"


def generate_barcode_image(
    code: str,
    format: str = "PNG",
    width: int = 300,
    height: int = 100,
) -> bytes:
    import barcode
    from barcode.writer import ImageWriter
    try:
        Code128 = barcode.get_barcode_class("code128")
        b = Code128(code, writer=ImageWriter())
        buf = io.BytesIO()
        b.write(buf, options={"module_width": 0.5, "module_height": 15.0})
        return buf.getvalue()
    except ImportError:
        logger.warning("python-barcode not installed, returning empty bytes")
        return b""
