#!/usr/bin/env bash
# =============================================================================
# GSF: scan-secrets.sh — Repository Secret Scanner
# =============================================================================
# Scans the repository for leaked secrets using gitleaks (preferred) or a
# Python-based fallback scanner.
#
# Usage:
#   ./scan-secrets.sh [path] [options]
#
# Arguments:
#   path          Repository root path (default: .)
#
# Options:
#   --json        Output results in JSON format
#   --sarif       Output results in SARIF format
#   --html        Output results in HTML format
#   --help, -h    Show this help message
#
# Environment:
#   GITLEAKS_PATH    Path to custom gitleaks binary
#
# Exit Codes:
#   0   No secrets found
#   1   Secrets found
#   2   Error during scanning
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPORT_DIR="${PROJECT_ROOT}/security/reports/secrets"

usage() {
    sed -n '/^# ============/,/^# ============/p' "${BASH_SOURCE[0]}" | \
        grep -v '^# ============' | sed 's/^# //'
    exit 0
}

log_info()  { echo "[INFO]  $*" >&2; }
log_warn()  { echo "[WARN]  $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

OUTPUT_FORMAT="json"
SCAN_PATH="."

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --json)    OUTPUT_FORMAT="json" ;;
        --sarif)   OUTPUT_FORMAT="sarif" ;;
        --html)    OUTPUT_FORMAT="html" ;;
        --*)
            log_error "Unknown option: $1"
            usage
            ;;
        *)
            if [[ -z "${SCAN_PATH}" ]] || [[ "${SCAN_PATH}" == "." ]]; then
                SCAN_PATH="$1"
            else
                log_error "Unexpected argument: $1"
                usage
            fi
            ;;
    esac
    shift
done

if [[ ! -d "${SCAN_PATH}" ]]; then
    log_error "Invalid scan path: ${SCAN_PATH}"
    exit 2
fi

mkdir -p "${REPORT_DIR}"

scan_with_gitleaks() {
    local gitleaks_bin
    gitleaks_bin="${GITLEAKS_PATH:-$(command -v gitleaks || true)}"

    if [[ -z "${gitleaks_bin}" ]]; then
        return 1
    fi

    if ! [[ -x "${gitleaks_bin}" ]]; then
        log_warn "Gitleaks binary not executable: ${gitleaks_bin}"
        return 1
    fi

    log_info "Using gitleaks: ${gitleaks_bin}"
    local config_path="${PROJECT_ROOT}/security/configs/.gitleaks.toml"
    local report_file="${REPORT_DIR}/secrets.${OUTPUT_FORMAT}"

    local format_flag
    case "${OUTPUT_FORMAT}" in
        json)  format_flag="--report-format=json" ;;
        sarif) format_flag="--report-format=sarif" ;;
        html)  format_flag="--report-format=json" ;;  # gitleaks doesn't support html, fallback
    esac

    local cmd_args=(
        "${gitleaks_bin}" detect
        "--source=${SCAN_PATH}"
        "${format_flag}"
        "--report-path=${report_file}"
        "--no-git"
        "--verbose"
    )

    if [[ -f "${config_path}" ]]; then
        cmd_args+=("--config=${config_path}")
    fi

    if "${cmd_args[@]}"; then
        log_info "Gitleaks scan completed: no secrets found"
        return 0
    else
        local exit_code=$?
        log_warn "Gitleaks scan completed: secrets detected"
        return "${exit_code}"
    fi
}

fallback_python_scan() {
    log_info "Using Python-based secret scanner (fallback)"

    local report_file="${REPORT_DIR}/secrets.${OUTPUT_FORMAT}"
    local python_script
    python_script=$(cat << 'PYEOF'
import argparse
import json
import os
import re
import sys
from pathlib import Path


SECRET_PATTERNS = [
    (r'(?i)api[_-]?key[=\s"'"'"']+[A-Za-z0-9_\-]{16,}', "API Key"),
    (r'(?i)secret[=\s"'"'"']+[A-Za-z0-9_\-!@#$%^&*()=+]{16,}', "Secret"),
    (r'(?i)password[=\s"'"'"']+[^,;\]\)\s]{8,}', "Password"),
    (r'(?i)token[=\s"'"'"']+[A-Za-z0-9_\-\.]{16,}', "Token"),
    (r'(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}', "Bearer Token"),
    (r'(?i)-----BEGIN\s+(RSA|EC|DSA|OPENSSH|PRIVATE)\s+KEY-----', "Private Key"),
    (r'(?i)ghp_[A-Za-z0-9]{36}', "GitHub Token"),
    (r'(?i)gho_[A-Za-z0-9]{36}', "GitHub OAuth Token"),
    (r'(?i)ghu_[A-Za-z0-9]{36}', "GitHub User Token"),
    (r'(?i)ghs_[A-Za-z0-9]{36}', "GitHub SSH Token"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    (r'(?i)sk-[a-zA-Z0-9]{32,}', "OpenAI API Key"),
    (r'(?i)eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', "JWT Token"),
    (r'slack-[a-zA-Z0-9]{8,}', "Slack Token"),
    (r'xox[baprs]-[0-9a-zA-Z]{10,}', "Slack Bot Token"),
    (r'(?i)mongodb\+srv://[^@]+@[^\s]+', "MongoDB Connection String"),
    (r'(?i)postgresql://[^:]+:[^@]+@[^\s]+', "PostgreSQL Connection String"),
    (r'(?i)redis://[^:]+:[^@]+@[^\s]+', "Redis Connection String"),
    (r'(?i)-----BEGIN CERTIFICATE-----', "Certificate"),
    (r'(?i)db_password[=\s"'"'"']+[^,;\]\)\s]{8,}', "Database Password"),
    (r'(?i)jwt_secret[=\s"'"'"']+[^,;\]\)\s]{16,}', "JWT Secret"),
    (r'(?i)session_secret[=\s"'"'"']+[^,;\]\)\s]{16,}', "Session Secret"),
    (r'(?i)encryption_key[=\s"'"'"']+[^,;\]\)\s]{16,}', "Encryption Key"),
    (r'gula_[a-zA-Z0-9]{32,64}', "GULA API Key"),
    (r'ROOT_URL=https?://[^\s]+', "Internal URL with potential credentials"),
]


EXCLUDE_PATTERNS = [
    r'vendor/',
    r'node_modules/',
    r'\.git/',
    r'__pycache__/',
    r'\.venv/',
    r'\.env\.example',
    r'\.env\.template',
    r'test_',
    r'/tests/',
    r'\.md$',
    r'\.rst$',
    r'poetry\.lock',
    r'package-lock\.json',
    r'yarn\.lock',
]


def should_exclude(filepath: str) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, filepath):
            return True
    return False


def scan_file(filepath: str) -> list[dict]:
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (IOError, OSError) as e:
        return [{"file": filepath, "error": str(e)}]

    for pattern, name in SECRET_PATTERNS:
        for match in re.finditer(pattern, content):
            line_num = content[:match.start()].count("\n") + 1
            start = max(0, match.start() - 40)
            end = min(len(content), match.end() + 40)
            context = content[start:end].replace("\n", " ").strip()
            findings.append({
                "file": filepath,
                "line": line_num,
                "type": name,
                "match": match.group()[:80],
                "context": context[:120],
            })
    return findings


def main():
    parser = argparse.ArgumentParser(description="Python-based secret scanner")
    parser.add_argument("path", nargs="?", default=".", help="Path to scan")
    parser.add_argument("--format", choices=["json", "sarif", "html"], default="json")
    parser.add_argument("--output", default=None, help="Output file")
    args = parser.parse_args()

    scan_root = Path(args.path).resolve()
    findings = []

    for root, dirs, files in os.walk(scan_root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "vendor", "__pycache__")]
        for fname in files:
            fpath = os.path.join(root, fname)
            if should_exclude(fpath):
                continue
            findings.extend(scan_file(fpath))

    output_file = args.output
    if args.format == "json":
        result = json.dumps({"findings": findings, "total": len(findings), "scanned_path": str(scan_root)}, indent=2)
        if output_file:
            with open(output_file, "w") as f:
                f.write(result)
        else:
            print(result)
    elif args.format == "sarif":
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {"driver": {"name": "GSF Secret Scanner", "version": "1.0.0"}},
                "results": [
                    {
                        "ruleId": f["type"],
                        "level": "error",
                        "message": {"text": f"Secret found: {f['type']}"},
                        "locations": [{
                            "physicalLocation": {
                                "artifactLocation": {"uri": f["file"]},
                                "region": {"startLine": f["line"]},
                            }
                        }],
                    }
                    for f in findings
                ],
            }]
        }
        result = json.dumps(sarif, indent=2)
        if output_file:
            with open(output_file, "w") as f:
                f.write(result)
        else:
            print(result)
    elif args.format == "html":
        html_parts = [
            "<!DOCTYPE html><html><head><title>Secret Scan Report</title>",
            "<style>body{font-family:sans-serif;margin:2em}"
            "table{border-collapse:collapse;width:100%}"
            "th,td{border:1px solid #ddd;padding:8px;text-align:left}"
            "th{background-color:#dc3545;color:white}"
            "tr:nth-child(even){background-color:#f2f2f2}</style></head><body>",
            f"<h1>Secret Scan Report</h1><p>Scan path: {scan_root}</p>",
            f"<p>Total findings: {len(findings)}</p>",
        ]
        if findings:
            html_parts.append("<table><tr><th>File</th><th>Line</th><th>Type</th><th>Match</th></tr>")
            for f in findings:
                html_parts.append(
                    f"<tr><td>{f['file']}</td><td>{f['line']}</td>"
                    f"<td>{f['type']}</td><td><code>{f['match'][:60]}</code></td></tr>"
                )
            html_parts.append("</table>")
        html_parts.append("</body></html>")
        result = "\n".join(html_parts)
        if output_file:
            with open(output_file, "w") as f:
                f.write(result)
        else:
            print(result)

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
PYEOF
)

    python3 -c "${python_script}" "${SCAN_PATH}" \
        --format "${OUTPUT_FORMAT}" \
        --output "${report_file}"
}

main() {
    local exit_code=0

    log_info "Starting secret scan of: ${SCAN_PATH}"
    log_info "Output format: ${OUTPUT_FORMAT}"
    log_info "Report directory: ${REPORT_DIR}"

    if scan_with_gitleaks; then
        log_info "Gitleaks scan completed successfully"
    else
        exit_code=$?
        if [[ ${exit_code} -eq 1 ]]; then
            log_warn "Secrets detected by gitleaks"
        else
            log_warn "Gitleaks failed (exit ${exit_code}), falling back to Python scanner"
            if fallback_python_scan; then
                log_info "Python fallback scan completed: no secrets found"
                exit_code=0
            else
                exit_code=$?
                log_warn "Secrets detected by Python fallback scanner"
            fi
        fi
    fi

    if [[ ${exit_code} -eq 1 ]]; then
        log_error "SECRETS FOUND in repository. Review and remediate immediately."
        cat "${REPORT_DIR}/secrets.${OUTPUT_FORMAT}" 2>/dev/null || true
    else
        log_info "No secrets detected. Repository is clean."
    fi

    exit "${exit_code}"
}

main
