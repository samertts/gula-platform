# GULA Laboratory Constitution

## Fundamental Role

The laboratory is the primary diagnostic engine of GULA. Laboratory data drives clinical decisions, public health surveillance, research, and quality improvement. The laboratory module must be the most reliable, most accurate, and most performant component of the platform. Events from laboratory operations follow Article 16 (Event Constitution).

## Specimen Integrity

1. **Chain of custody** is maintained from collection through disposal. Every specimen handling event (collection, transport, receipt, processing, storage, disposal) is recorded with responsible party, timestamp, and condition.

2. **Specimen identification** uses barcode/QR labeling with human-readable fallback. Labels survive freezing, thawing, and laboratory solvents.

3. **Rejection criteria** for unacceptable specimens are configurable per laboratory and enforced at receipt. Rejection reason is documented and communicated to the ordering clinician.

## Order Management

4. **Order entry** captures patient identification, test selection, clinical indication, urgency, collection requirements, and billing codes in a single workflow.

5. **Order sets** group commonly ordered tests by clinical context (pre-operative, diabetic panel, infectious workup) with evidence-based defaults.

6. **Order verification** validates patient identity, test availability, consent status, and insurance coverage before submission.

## Result Management

7. **Result entry** supports manual entry, batch upload, and instrument interface with automatic validation rules.

8. **Delta checks** compare results against previous results for the same patient and test. Significant changes are flagged for review.

9. **Reference ranges** are age-specific, sex-specific, and pregnancy-specific where applicable. Ranges are versioned and traceable.

10. **Critical value notification** follows mandatory escalation with acknowledgment tracking. Unacknowledged criticals escalate at 15 and 30 minutes.

## Quality Control

11. **Internal quality control (IQC)** results are recorded, plotted (Levey-Jennings), and evaluated against Westgard rules. QC violations lock result reporting for the affected test.

12. **External quality assessment (EQA)** participation is tracked per test with performance scoring and corrective action documentation.

13. **Instrument calibration** and maintenance are scheduled, tracked, and enforced. Results from uncalibrated instruments are blocked.

## Instrument Integration

14. **Device bridge** (ASTM/HL7) connects laboratory instruments to GULA. Results from connected instruments are auto-validated and auto-posted where appropriate.

15. **Device monitoring** tracks instrument status, error states, consumable levels, and maintenance schedules.

16. **Bidirectional communication** enables the platform to send orders to instruments where the instrument supports it.

## Laboratory Administration

17. **Panel management** defines test panels with component tests, calculated results, and reflex testing rules.

18. **Test catalog** maintains test definitions, methodologies, units, reference ranges, and billing codes.

19. **Workload management** distributes work across technicians, tracks turnaround times, and identifies bottlenecks.

20. **Inventory management** tracks reagents, consumables, and supplies with low-stock alerts and usage forecasting.
