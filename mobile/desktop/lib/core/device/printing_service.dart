
import 'package:flutter/foundation.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';


class PrintingService {
  Future<void> printPdf(Uint8List pdfData, {String jobName = 'GULA Report'}) async {
    try {
      await Printing.layoutPdf(
        onLayout: (_) => pdfData,
        name: jobName,
      );
    } catch (e) {
      debugPrint('Print error: $e');
      rethrow;
    }
  }

  Future<Uint8List> generateReportPdf({
    required String title,
    required String patientName,
    required String patientId,
    required String date,
    required String labName,
    required List<Map<String, String>> results,
    String? notes,
  }) async {
    final pdf = pw.Document();

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(32),
        header: (context) => pw.Header(
          level: 0,
          child: pw.Text(
            labName,
            style: pw.TextStyle(fontSize: 18, fontWeight: pw.FontWeight.bold),
          ),
        ),
        footer: (context) => pw.Text(
          'Page ${context.pageNumber} of ${context.pagesCount}',
          style: const pw.TextStyle(fontSize: 10),
        ),
        build: (context) => [
          pw.Header(level: 1, text: title),
          pw.SizedBox(height: 16),
          pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text('Patient: $patientName'),
                  pw.Text('ID: $patientId'),
                ],
              ),
              pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.end,
                children: [
                  pw.Text('Date: $date'),
                ],
              ),
            ],
          ),
          pw.SizedBox(height: 24),
          pw.TableHelper.fromTextArray(
            headers: ['Test', 'Result', 'Unit', 'Reference Range', 'Flag'],
            data: results.map((r) => [
              r['test'] ?? '',
              r['result'] ?? '',
              r['unit'] ?? '',
              r['reference'] ?? '',
              r['flag'] ?? '',
            ]).toList(),
            headerStyle: pw.TextStyle(fontWeight: pw.FontWeight.bold),
            border: pw.TableBorder.all(),
            headerDecoration: const pw.BoxDecoration(color: PdfColors.grey200),
            cellAlignment: pw.Alignment.centerLeft,
          ),
          if (notes != null && notes.isNotEmpty) ...[
            pw.SizedBox(height: 16),
            pw.Text('Notes: $notes'),
          ],
          pw.SizedBox(height: 32),
          pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
            children: [
              pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text('____________________'),
                  pw.Text('Performed By'),
                ],
              ),
              pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text('____________________'),
                  pw.Text('Validated By'),
                ],
              ),
            ],
          ),
        ],
      ),
    );

    return await pdf.save();
  }

  Future<Uint8List> generateBarcodeLabel({
    required String barcode,
    required String patientName,
    required String sampleType,
    required String date,
  }) async {
    final pdf = pw.Document();

    pdf.addPage(
      pw.Page(
        pageFormat: PdfPageFormat(100 * PdfPageFormat.mm, 50 * PdfPageFormat.mm),
        margin: const pw.EdgeInsets.all(4),
        build: (context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.center,
          mainAxisAlignment: pw.MainAxisAlignment.center,
          children: [
            pw.BarcodeWidget(
              barcode: pw.Barcode.code128(),
              data: barcode,
              width: 80 * PdfPageFormat.mm,
              height: 15 * PdfPageFormat.mm,
            ),
            pw.SizedBox(height: 4),
            pw.Text(barcode, style: const pw.TextStyle(fontSize: 10)),
            pw.SizedBox(height: 2),
            pw.Text(patientName, style: const pw.TextStyle(fontSize: 8)),
            pw.Text('$sampleType | $date', style: const pw.TextStyle(fontSize: 7)),
          ],
        ),
      ),
    );

    return await pdf.save();
  }

  Future<void> printLabel({
    required String barcode,
    required String patientName,
    required String sampleType,
    required String date,
  }) async {
    final pdfData = await generateBarcodeLabel(
      barcode: barcode,
      patientName: patientName,
      sampleType: sampleType,
      date: date,
    );
    await printPdf(pdfData, jobName: 'Sample Label - $barcode');
  }

  Future<void> printReceipt(Map<String, dynamic> receiptData) async {
    final pdf = pw.Document();

    pdf.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.roll80,
        margin: const pw.EdgeInsets.all(8),
        build: (context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.center,
          children: [
            pw.Text('GULA Platform',
                style: const pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold)),
            pw.Divider(),
            pw.Text('Receipt #${receiptData['receipt_number'] ?? ''}'),
            pw.Text('Date: ${receiptData['date'] ?? ''}'),
            pw.Divider(),
            ...((receiptData['items'] as List?) ?? []).map((item) => pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text(item['name']?.toString() ?? ''),
                pw.Text('${item['quantity'] ?? ''} x ${item['price'] ?? ''}'),
              ],
            )),
            pw.Divider(),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('Total:',
                    style: const pw.TextStyle(fontWeight: pw.FontWeight.bold)),
                pw.Text('${receiptData['total'] ?? ''} IQD',
                    style: const pw.TextStyle(fontWeight: pw.FontWeight.bold)),
              ],
            ),
            pw.SizedBox(height: 16),
            pw.Text('Thank you for your visit'),
          ],
        ),
      ),
    );

    await printPdf(await pdf.save(), jobName: 'Receipt');
  }
}
