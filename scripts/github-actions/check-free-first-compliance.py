#!/usr/bin/env python3
"""Check Free First Compliance - no paid services in requirements."""
import re
import pathlib
import sys

paid_patterns = [
    r'(openai|anthropic|google\.ai|aws|azure|gcp)\.(com|io)',
    r'stripe\.com', r'twilio\.com', r'sendgrid\.net',
    r'auth0\.com', r'okta\.com', r'supabase\.(co|com)',
    r'firebase\.(io|googleapis\.com)',
]

issues = []
for f in pathlib.Path('.').rglob('requirements*.txt'):
    text = f.read_text()
    for pat in paid_patterns:
        if re.search(pat, text, re.I):
            issues.append(f'{f}: {pat}')

for f in pathlib.Path('.').rglob('package.json'):
    if 'node_modules' in str(f):
        continue
    text = f.read_text()
    for pat in paid_patterns:
        if re.search(pat, text, re.I):
            issues.append(f'{f}: {pat}')

if issues:
    print('PAID SERVICE VIOLATIONS:')
    for i in issues:
        print(f'  {i}')
    sys.exit(1)
print('Free First Compliance: PASS')
