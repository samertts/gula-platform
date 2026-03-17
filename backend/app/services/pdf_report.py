"""Generate professional lab result PDF reports with QR code."""
import io
import qrcode
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def generate_result_pdf(data: dict, result_url: str) -> bytes:
    """Generate a PDF report for lab results.

    Args:
        data: Result data dict (same format as /r/{token} response)
        result_url: Full URL to the result page for QR code

    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=15 * mm, bottomMargin=15 * mm,
                            leftMargin=15 * mm, rightMargin=15 * mm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', parent=styles['Title'],
                              alignment=TA_CENTER, fontSize=20, spaceAfter=2))
    styles.add(ParagraphStyle(name='CenterSub', parent=styles['Normal'],
                              alignment=TA_CENTER, fontSize=10, textColor=colors.grey))
    styles.add(ParagraphStyle(name='RightAlign', parent=styles['Normal'],
                              alignment=TA_RIGHT, fontSize=9))
    styles.add(ParagraphStyle(name='SmallGrey', parent=styles['Normal'],
                              fontSize=8, textColor=colors.grey))
    styles.add(ParagraphStyle(name='Disclaimer', parent=styles['Normal'],
                              fontSize=7, textColor=colors.grey, alignment=TA_CENTER))

    elements = []

    # Header
    elements.append(Paragraph("GULA", styles['CenterTitle']))
    elements.append(Paragraph("Smart Health Platform - Lab Result Report", styles['CenterSub']))
    elements.append(Spacer(1, 8 * mm))

    # Lab & Patient info
    patient = data.get("patient", {})
    lab = data.get("lab", {})
    order_date = data.get("order_date", "")
    doctor = data.get("doctor_name", "")

    if order_date:
        try:
            order_date = datetime.fromisoformat(order_date).strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            pass

    info_data = [
        [Paragraph(f"<b>Patient:</b> {patient.get('name', '-')}", styles['Normal']),
         Paragraph(f"<b>Laboratory:</b> {lab.get('name', '-')}", styles['RightAlign'])],
        [Paragraph(f"<b>Health ID:</b> {patient.get('health_id', '-')}", styles['Normal']),
         Paragraph(f"<b>City:</b> {lab.get('city', '-')}", styles['RightAlign'])],
        [Paragraph(f"<b>Date:</b> {order_date}", styles['Normal']),
         Paragraph(f"<b>Doctor:</b> {doctor or '-'}", styles['RightAlign'])],
    ]
    info_table = Table(info_data, colWidths=[doc.width * 0.5, doc.width * 0.5])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    # Results table
    results = data.get("results", [])
    table_data = [["Test Name", "Value", "Unit", "Normal Range", "Status"]]

    for r in results:
        value = str(r.get("value", "")) if r.get("value") is not None else (r.get("value_text") or "-")
        unit = r.get("unit") or ""
        low = r.get("normal_range_low")
        high = r.get("normal_range_high")
        normal_range = f"{low} - {high}" if low is not None and high is not None else "-"

        flag = r.get("flag", "")
        flag_display = {
            "normal": "Normal",
            "H": "High",
            "L": "Low",
            "critical": "CRITICAL",
        }.get(flag, flag or "-")

        table_data.append([
            r.get("test_name", "-"),
            value,
            unit,
            normal_range,
            flag_display,
        ])

    result_table = Table(table_data, colWidths=[
        doc.width * 0.28, doc.width * 0.15, doc.width * 0.15,
        doc.width * 0.22, doc.width * 0.20
    ])

    # Style the results table
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]

    # Color-code status column
    for i, r in enumerate(results, start=1):
        flag = r.get("flag", "")
        if flag == "critical":
            table_style.append(('TEXTCOLOR', (4, i), (4, i), colors.HexColor('#dc2626')))
            table_style.append(('FONTNAME', (4, i), (4, i), 'Helvetica-Bold'))
        elif flag == "H":
            table_style.append(('TEXTCOLOR', (4, i), (4, i), colors.HexColor('#ef4444')))
        elif flag == "L":
            table_style.append(('TEXTCOLOR', (4, i), (4, i), colors.HexColor('#3b82f6')))
        elif flag == "normal":
            table_style.append(('TEXTCOLOR', (4, i), (4, i), colors.HexColor('#16a34a')))

    result_table.setStyle(TableStyle(table_style))
    elements.append(result_table)
    elements.append(Spacer(1, 6 * mm))

    # Interpretations section
    for r in results:
        interp = r.get("interpretation")
        if interp:
            elements.append(Paragraph(
                f"<b>{r.get('test_name', '')}:</b> {interp.get('interpretation', '')} - {interp.get('advice', '')}",
                styles['SmallGrey']
            ))
            elements.append(Spacer(1, 1 * mm))

    elements.append(Spacer(1, 6 * mm))

    # QR Code
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(result_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    qr_image = Image(qr_buffer, width=30 * mm, height=30 * mm)

    qr_table = Table(
        [[qr_image, Paragraph(
            f"Scan to view results online<br/><font size='7' color='grey'>{result_url}</font>",
            styles['Normal']
        )]],
        colWidths=[35 * mm, doc.width - 40 * mm]
    )
    qr_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (1, 0), (1, 0), 10),
    ]))
    elements.append(qr_table)
    elements.append(Spacer(1, 6 * mm))

    # Disclaimer
    elements.append(Paragraph(
        "This report is for informational purposes only. It is not a medical diagnosis. Please consult your doctor.",
        styles['Disclaimer']
    ))
    elements.append(Paragraph(
        "هذا التقرير لأغراض إعلامية فقط. ليس تشخيصاً طبياً. يرجى مراجعة طبيبك.",
        styles['Disclaimer']
    ))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(
        f"Generated by GULA Platform - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles['Disclaimer']
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
