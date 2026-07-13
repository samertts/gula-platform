"""Generate professional bilingual (Arabic/English) lab result PDF reports.

Arabic text handling:
- arabic_reshaper: Connects Arabic letters (Arabic is a connected script)
- python-bidi: Applies Unicode BiDi algorithm for right-to-left rendering
- DejaVu / Noto fonts: Unicode TTF fonts with Arabic glyph coverage

Both are required for correct Arabic rendering in ReportLab.
"""

import io
import logging
import os
from datetime import datetime

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app._compat import UTC

logger = logging.getLogger("gula.pdf")

# ─── Arabic Font Registration ─────────────────────────────────────────────────
# Search for a Unicode font with Arabic coverage installed by Dockerfile
_FONT_SEARCH_PATHS = [
    # Noto fonts (fonts-noto-core package)
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    # DejaVu fonts (fonts-dejavu-core package)
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    # Fallback system paths
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/noto/NotoSans-Regular.ttf",
]

_ARABIC_FONT = "Helvetica"  # Fallback if no Arabic font found
_ARABIC_FONT_BOLD = "Helvetica-Bold"
_ARABIC_AVAILABLE = False

for _path in _FONT_SEARCH_PATHS:
    if os.path.exists(_path):
        try:
            pdfmetrics.registerFont(TTFont("GulaArabic", _path))
            _ARABIC_FONT = "GulaArabic"
            _ARABIC_FONT_BOLD = "GulaArabic"
            _ARABIC_AVAILABLE = True
            logger.info("Arabic font registered: %s", _path)
            break
        except Exception as e:
            logger.warning("Could not register font %s: %s", _path, e)


def _ar(text: str) -> str:
    """Reshape and apply BiDi algorithm to Arabic text for correct PDF rendering.

    Without this, Arabic appears as disconnected reversed characters.
    """
    if not text or not _ARABIC_AVAILABLE:
        return text or ""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except ImportError:
        return text


def _hijri_date(dt: datetime) -> str:
    """Convert Gregorian datetime to Hijri date string.

    Returns empty string if hijri-converter is not available.
    """
    try:
        from hijri_converter import convert

        h = convert.Gregorian(dt.year, dt.month, dt.day).to_hijri()
        return f"{h.day}/{h.month}/{h.year} هـ"
    except (ImportError, Exception):
        return ""


# ─── Status flag mappings ─────────────────────────────────────────────────────
_FLAG_EN = {
    "normal": "Normal",
    "N": "Normal",
    "high": "High ↑",
    "H": "High ↑",
    "low": "Low ↓",
    "L": "Low ↓",
    "critical_high": "CRITICAL HIGH ↑↑",
    "HH": "CRITICAL HIGH ↑↑",
    "critical_low": "CRITICAL LOW ↓↓",
    "LL": "CRITICAL LOW ↓↓",
    "critical": "CRITICAL",
}
_FLAG_AR = {
    "normal": "طبيعي",
    "N": "طبيعي",
    "high": "مرتفع ↑",
    "H": "مرتفع ↑",
    "low": "منخفض ↓",
    "L": "منخفض ↓",
    "critical_high": "بالغ الارتفاع ↑↑",
    "HH": "بالغ الارتفاع ↑↑",
    "critical_low": "بالغ الانخفاض ↓↓",
    "LL": "بالغ الانخفاض ↓↓",
    "critical": "حرج",
}
_FLAG_COLORS = {
    "normal": colors.HexColor("#16a34a"),
    "N": colors.HexColor("#16a34a"),
    "high": colors.HexColor("#ef4444"),
    "H": colors.HexColor("#ef4444"),
    "low": colors.HexColor("#3b82f6"),
    "L": colors.HexColor("#3b82f6"),
    "critical_high": colors.HexColor("#dc2626"),
    "HH": colors.HexColor("#dc2626"),
    "critical_low": colors.HexColor("#dc2626"),
    "LL": colors.HexColor("#dc2626"),
    "critical": colors.HexColor("#dc2626"),
}


def generate_result_pdf(data: dict, result_url: str) -> bytes:
    """Generate a bilingual Arabic/English lab result PDF.

    Args:
        data: Result data dict (same format as /r/{token} response)
        result_url: Full URL to the result page for QR code

    Returns:
        PDF as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    # ─── Styles ───────────────────────────────────────────────────────────────
    W = doc.width

    def style(name, **kwargs):
        return ParagraphStyle(name=name, **kwargs)

    s_title = style(
        "GulaCenterTitle",
        fontName=_ARABIC_FONT_BOLD,
        fontSize=22,
        alignment=TA_CENTER,
        spaceAfter=2,
        textColor=colors.HexColor("#1e40af"),
    )
    s_subtitle = style(
        "GulaSubtitle",
        fontName=_ARABIC_FONT,
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey,
    )
    s_normal = style("GulaNormal", fontName=_ARABIC_FONT, fontSize=9)
    s_right = style("GulaRight", fontName=_ARABIC_FONT, fontSize=9, alignment=TA_RIGHT)
    s_center = style("GulaCenter", fontName=_ARABIC_FONT, fontSize=9, alignment=TA_CENTER)

    s_small = style("GulaSmall", fontName=_ARABIC_FONT, fontSize=7, textColor=colors.grey)
    s_disclaimer = style(
        "GulaDisclaimer",
        fontName=_ARABIC_FONT,
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    s_arabic = style(
        "GulaArabic", fontName=_ARABIC_FONT, fontSize=9, alignment=TA_RIGHT, rightIndent=0
    )
    s_section = style(
        "GulaSection",
        fontName=_ARABIC_FONT_BOLD,
        fontSize=10,
        textColor=colors.HexColor("#1e40af"),
        spaceBefore=4,
        spaceAfter=2,
    )

    elements = []

    # ─── Header ───────────────────────────────────────────────────────────────
    elements.append(Paragraph("GULA", s_title))
    elements.append(
        Paragraph(
            _ar("منصة غولا الصحية - تقرير نتائج المختبر") + " | Smart Health Platform",
            s_subtitle,
        )
    )
    elements.append(Spacer(1, 3 * mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e40af")))
    elements.append(Spacer(1, 5 * mm))

    # ─── Patient / Lab Info (bilingual two-column) ────────────────────────────
    patient = data.get("patient", {})
    lab = data.get("lab", {})
    order_date_raw = data.get("order_date", "")
    doctor = data.get("doctor_name", "")

    gregorian_date = ""
    hijri_date_str = ""
    if order_date_raw:
        try:
            dt = datetime.fromisoformat(order_date_raw)
            gregorian_date = dt.strftime("%Y-%m-%d %H:%M")
            hijri_date_str = _hijri_date(dt)
        except (ValueError, TypeError):
            gregorian_date = str(order_date_raw)

    patient_name = patient.get("name", "-")
    health_id = patient.get("health_id", "-")
    lab_name = lab.get("name", "-")
    lab_city = lab.get("city", "-")

    info_rows = [
        [
            Paragraph(f"<b>Patient / المريض:</b> {patient_name}", s_normal),
            Paragraph(_ar(f"المختبر: {lab_name}") + f" / Lab: {lab_name}", s_right),
        ],
        [
            Paragraph(f"<b>Health ID / الرقم الصحي:</b> {health_id}", s_normal),
            Paragraph(_ar(f"المدينة: {lab_city}") + f" / City: {lab_city}", s_right),
        ],
        [
            Paragraph(f"<b>Date / التاريخ:</b> {gregorian_date}", s_normal),
            Paragraph(
                (_ar(f"التاريخ الهجري: {hijri_date_str}") if hijri_date_str else "")
                + (f" / Doctor: {doctor}" if doctor else ""),
                s_right,
            ),
        ],
    ]
    info_table = Table(info_rows, colWidths=[W * 0.55, W * 0.45])
    info_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    # ─── Results Table ────────────────────────────────────────────────────────
    elements.append(
        Paragraph(
            _ar("نتائج التحاليل") + " / Lab Results",
            s_section,
        )
    )

    results = data.get("results", [])
    headers = [
        Paragraph(f"<b>Test / {_ar('الفحص')}</b>", s_center),
        Paragraph(f"<b>Value / {_ar('القيمة')}</b>", s_center),
        Paragraph(f"<b>Unit / {_ar('الوحدة')}</b>", s_center),
        Paragraph(f"<b>Range / {_ar('المدى الطبيعي')}</b>", s_center),
        Paragraph(f"<b>Status / {_ar('الحالة')}</b>", s_center),
    ]
    table_data = [headers]
    table_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), _ARABIC_FONT_BOLD),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
    ]

    for i, r in enumerate(results, start=1):
        flag = r.get("flag", "") or ""
        value = (
            str(r.get("value", "")) if r.get("value") is not None else (r.get("value_text") or "-")
        )
        unit = r.get("unit") or ""
        low = r.get("normal_range_low")
        high = r.get("normal_range_high")
        normal_range = f"{low} - {high}" if low is not None and high is not None else "-"

        flag_en = _FLAG_EN.get(flag, flag or "-")
        flag_ar = _FLAG_AR.get(flag, "")
        flag_display = f"{flag_en}\n{_ar(flag_ar)}" if flag_ar else flag_en

        row = [
            Paragraph(r.get("test_name", "-"), s_normal),
            Paragraph(f"<b>{value}</b>", s_center),
            Paragraph(unit, s_center),
            Paragraph(normal_range, s_center),
            Paragraph(flag_display, s_center),
        ]
        table_data.append(row)

        # Color-code status column
        flag_color = _FLAG_COLORS.get(flag)
        if flag_color:
            table_styles.append(("TEXTCOLOR", (4, i), (4, i), flag_color))
            if "critical" in flag.lower():
                table_styles.append(("FONTNAME", (4, i), (4, i), _ARABIC_FONT_BOLD))
                table_styles.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fef2f2")))

    result_table = Table(
        table_data,
        colWidths=[W * 0.26, W * 0.14, W * 0.14, W * 0.24, W * 0.22],
    )
    result_table.setStyle(TableStyle(table_styles))
    elements.append(result_table)
    elements.append(Spacer(1, 5 * mm))

    # ─── Clinical Interpretations (if any) ───────────────────────────────────
    interps = [
        (r.get("test_name"), r.get("interpretation")) for r in results if r.get("interpretation")
    ]
    if interps:
        elements.append(
            Paragraph(
                _ar("ملاحظات سريرية") + " / Clinical Notes",
                s_section,
            )
        )
        for test_name, interp in interps:
            ar_interp = interp.get("interpretation_ar") or interp.get("interpretation", "")
            en_interp = interp.get("interpretation", "")
            advice_ar = interp.get("advice_ar") or interp.get("advice", "")

            elements.append(
                Paragraph(
                    f"<b>{test_name}:</b> {en_interp}"
                    + (f" — {_ar(ar_interp)}" if ar_interp and _ARABIC_AVAILABLE else ""),
                    s_small,
                )
            )
            if advice_ar and _ARABIC_AVAILABLE:
                elements.append(Paragraph(_ar(advice_ar), s_arabic))
            elements.append(Spacer(1, 1 * mm))

    elements.append(Spacer(1, 5 * mm))

    # ─── QR Code + Scan Instructions ──────────────────────────────────────────
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(result_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    qr_image = Image(qr_buf, width=28 * mm, height=28 * mm)

    scan_text = (
        _ar("امسح الرمز لعرض النتائج إلكترونياً") + f"<br/>Scan QR to view results online<br/>"
        f"<font size='7' color='grey'>{result_url}</font>"
    )
    qr_row = Table(
        [[qr_image, Paragraph(scan_text, s_normal)]],
        colWidths=[33 * mm, W - 38 * mm],
    )
    qr_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (1, 0), (1, 0), 8),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ]
        )
    )
    elements.append(qr_row)
    elements.append(Spacer(1, 5 * mm))

    # ─── Footer ───────────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    elements.append(Spacer(1, 2 * mm))
    elements.append(
        Paragraph(
            _ar("هذا التقرير لأغراض إعلامية فقط وليس تشخيصاً طبياً. يرجى مراجعة طبيبك."),
            s_disclaimer,
        )
    )
    elements.append(
        Paragraph(
            "This report is for informational purposes only. Not a medical diagnosis. Consult your doctor.",
            s_disclaimer,
        )
    )
    elements.append(Spacer(1, 1 * mm))
    elements.append(
        Paragraph(
            f"Generated by GULA Platform — {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')} UTC",
            s_disclaimer,
        )
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
