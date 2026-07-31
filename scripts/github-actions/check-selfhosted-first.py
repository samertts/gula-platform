#!/usr/bin/env python3
"""Check Self-Hosted First compliance."""
import pathlib

saas_refs = ["supabase", "firebase", "auth0", "okta",
             "aws.amazon", "azure.microsoft", "cloud.google",
             "mongodb.com/atlas", "datadog", "newrelic"]

issues = []
for f in list(pathlib.Path("backend").rglob("*.py")) + list(pathlib.Path(".github").rglob("*.yml")):
    t = f.read_text().lower()
    for p in saas_refs:
        if p in t:
            issues.append(f'{f.relative_to(pathlib.Path("."))}: references {p}')

for i in issues:
    print(f"  WARNING: {i}")
print("Self-Hosted First: PASS" if not issues else "Self-Hosted First: WARN")
