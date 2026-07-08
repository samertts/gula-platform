# Assessment Reports

## Purpose
Auto-generated assessment reports are placed here. Each report is timestamped and immutable.

## Available Reports

| Report | Frequency | Generator |
|--------|-----------|-----------|
| `full-assessment-<date>.md` | On demand | `assessment/scripts/generate-assessment.sh` |
| `coverage-<date>.md` | On demand | `assessment/scripts/coverage-report.sh` |
| `security-scan-<date>.md` | On demand | `assessment/scripts/security-scan.sh` |
| `compliance-<date>.md` | On demand | `assessment/scripts/compliance-check.sh` |

## Generation

```bash
# Generate full assessment
./assessment/scripts/generate-assessment.sh

# Generate individual reports
./assessment/scripts/coverage-report.sh
./assessment/scripts/security-scan.sh
./assessment/scripts/compliance-check.sh
```
