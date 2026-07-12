from __future__ import annotations

import io
import logging
from typing import Any

logger = logging.getLogger("gula.qr")


def generate_qr(
    data: str,
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "M",
) -> Any:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
    ec_map = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M, "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}
    qr = qrcode.QRCode(
        version=None,
        box_size=box_size,
        border=border,
        error_correction=ec_map.get(error_correction, ERROR_CORRECT_M),
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr


def generate_qr_image(
    data: str,
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "M",
    format: str = "PNG",
) -> bytes:
    qr = generate_qr(data, box_size, border, error_correction)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def generate_qr_svg(
    data: str,
    box_size: int = 10,
    border: int = 4,
    error_correction: str = "M",
) -> str:
    qr = generate_qr(data, box_size, border, error_correction)
    return qr.make_image().to_string()
