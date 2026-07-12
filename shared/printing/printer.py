from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("gula.printing")


@dataclass
class PrintJob:
    content: bytes
    job_type: str = "label"
    copies: int = 1
    printer_name: str = "default"


def print_label(data: str, barcode: str = "", copies: int = 1) -> bool:
    from shared.qr import generate_qr_image
    try:
        qr_bytes = generate_qr_image(data, box_size=6, border=2)
        job = PrintJob(content=qr_bytes, job_type="label", copies=copies)
        logger.info("[PRINT] Label job queued: %s", barcode or data[:20])
        return True
    except Exception as exc:
        logger.error("Print label failed: %s", exc)
        return False


def print_report(pdf_bytes: bytes, copies: int = 1) -> bool:
    job = PrintJob(content=pdf_bytes, job_type="report", copies=copies)
    logger.info("[PRINT] Report job queued (%d copies)", copies)
    return True
