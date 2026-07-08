# Assessment Scripts

## Purpose
Automation scripts for generating assessment reports and validating platform health.

## Scripts

| Script | Purpose |
|--------|---------|
| `generate-assessment.sh` | Generate complete engineering assessment report |
| `coverage-report.sh` | Generate test coverage report with per-module breakdown |
| `security-scan.sh` | Run Bandit SAST scan and format results |
| `compliance-check.sh` | Verify compliance with regulatory requirements |
| `architecture-validate.sh` | Validate architecture boundaries and layering |
| `database-check.sh` | Check database schema and migration health |
| `performance-baseline.sh` | Run performance baseline tests |

## Usage

```bash
# Generate everything
./assessment/scripts/generate-assessment.sh

# Individual reports
./assessment/scripts/coverage-report.sh
./assessment/scripts/security-scan.sh
./assessment/scripts/compliance-check.sh
```

## Requirements

- Python 3.11+ (`.venv` at project root)
- Bandit (`pip install bandit`)
- Coverage (`pip install pytest-cov`)
- Network access to PostgreSQL and Redis for full reports
