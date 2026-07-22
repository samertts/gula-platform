# GULA Clinical Constitution

## Patient Safety

1. **No change may introduce clinical risk.** All features that affect patient care — order entry, result reporting, reference ranges, clinical decision support — must be reviewed by a qualified clinician before deployment.

2. **Result integrity is absolute.** Lab results, imaging reports, pathology findings, and clinical observations must be transmitted, stored, and displayed without alteration. Version history preserves the full audit trail of corrections.

3. **Critical result escalation** follows a mandatory protocol: result verification → immediate notification → escalation within 15 minutes if unacknowledged → documented audit trail.

4. **Clinical decision support (CDS)** must be evidence-based, clearly attributed to sources, and reviewable by clinicians. CDS rules must not override clinical judgment without override documentation. AI-assisted CDS follows Article 11 (AI Constitution).

## Data Quality

5. **Every clinical data point is attributed** to the originating clinician, device, or system with timestamp accuracy to the second.

6. **Reference ranges are versioned** and traceable to source publications, laboratory validations, or instrument specifications.

7. **Data validation** ensures that out-of-range results, impossible values (e.g., negative hemoglobin), and incompatible units are flagged before persistence.

8. **Duplicate detection** prevents multiple records for the same patient, order, or result from being created without explicit confirmation.

## Clinical Workflow

9. **Order entry** supports order sets, clinical pathways, and evidence-based ordering. Orders are verified against formularies, drug interactions, and patient allergies.

10. **Result review** provides longitudinal context with trend visualization, delta checks, and comparison to previous results.

11. **Clinical notes** follow structured templates that capture relevant data elements without restricting narrative expression.

12. **Handover and transitions** are supported with structured summaries, task ownership, and accountability tracking.

## Patient Engagement

13. **Patients have access to their own results** through the citizen portal. Sensitive results may have a delayed release to allow clinician pre-notification.

14. **Patient-uploaded data** is clearly labeled as patient-provided and never commingled with clinical data without verification.

15. **Consent preferences** are respected across all data sharing, research participation, and public health reporting workflows.
