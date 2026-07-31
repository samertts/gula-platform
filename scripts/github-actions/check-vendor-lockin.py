#!/usr/bin/env python3
"""Check No Vendor Lock-In compliance."""
import pathlib
import re
import sys

vendor_sdks = [
    (r"import\s+boto3", "AWS SDK (boto3)"),
    (r"from\s+boto3", "AWS SDK (boto3)"),
    (r"from\s+azure\.", "Azure SDK"),
    (r"import\s+azure\.", "Azure SDK"),
    (r"from\s+google\.cloud", "GCP SDK"),
    (r"import\s+google\.cloud", "GCP SDK"),
    (r"import\s+supabase", "Supabase SDK"),
    (r"from\s+supabase", "Supabase SDK"),
    (r"import\s+auth0", "Auth0 SDK"),
    (r"from\s+auth0", "Auth0 SDK"),
    (r"import\s+okta", "Okta SDK"),
    (r"from\s+okta", "Okta SDK"),
    (r"import\s+stripe", "Stripe SDK"),
    (r"from\s+stripe", "Stripe SDK"),
]

issues = []
for f in pathlib.Path("backend/app").rglob("*.py"):
    text = f.read_text()
    rel = f.relative_to(pathlib.Path("."))
    for pat, name in vendor_sdks:
        if re.search(pat, text):
            issues.append(f"{rel}: {name}")

if issues:
    for issue in issues:
        print(f"  FAIL: {issue}")
    print("Vendor Lock-In: FAIL")
    sys.exit(1)
print("Vendor Lock-In: PASS")
