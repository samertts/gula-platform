# GULA CLI

Command-line interface for the GULA Platform — laboratory information
management from the terminal.

## Installation

```bash
pip install .
```

## Usage

### Configuration

```bash
# Set API base URL
gula configure --base-url https://api.example.com

# Or via environment variable
export GULA_BASE_URL=https://api.example.com

# Show current config
gula configure
```

### Authentication

```bash
# Login (prompts for email/password)
gula auth login

# With inline credentials
gula auth login --email user@lab.com --password s3cret

# Refresh stored token
gula auth refresh
```

### Patients

```bash
# List patients (paginated)
gula patients list
gula patients list --page 2 --limit 20
gula patients list --search "Ahmed"
gula patients list --table

# Get patient by ID
gula patients get 42

# Create patient (interactive)
echo '{"full_name": "Ali", "phone": "07701234567"}' | gula patients create

# Create patient (inline JSON)
gula patients create --json '{"full_name": "Ali", "phone": "07701234567"}'

# Create patient (from file)
gula patients create --json file://./patient.json
```

### Orders

```bash
gula orders list --table
gula orders get 123
gula orders create --json '{"patient_id": 42, "tests": ["CBC"]}'
```

### Results

```bash
gula results list --table
gula results get 456
```

### Labs

```bash
gula labs list --table
gula labs get 1
```

### Samples

```bash
gula samples list --table
gula samples get 789
```

### Consent

```bash
gula consent grant --json '{"gpid": "...", "grantee_id": "user:42", "scope": "lab:7", "expires_in_hours": 24}'
gula consent check --gpid "..." --scope "lab:7"
```

### Claims

```bash
gula claims list --table
gula claims create --json '{"patient_id": 1, "items": [{"test_code": "CBC", "unit_price": 10, "amount": 10}]}'
```

### Edge

```bash
gula edge devices --table
gula edge tasks --table
```

### Compliance / FHIR

```bash
gula compliance fhir patient PAT001
gula compliance fhir observation OBS001
```

### MPI

```bash
gula mpi --json '{"lab_id": 1, "patient_id": 42}'
```

### Statistics

```bash
gula stats dashboard
```

### System

```bash
gula health
gula test-types --table
gula --version
gula --help
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0    | Success |
| 1    | API error or config error |

## Environment Variables

| Variable         | Default               | Description    |
|------------------|-----------------------|----------------|
| `GULA_BASE_URL`  | `http://localhost:8000` | API base URL  |

## Development

```bash
pip install -e .
gula --help
```
