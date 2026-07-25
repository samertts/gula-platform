#!/usr/bin/env python3
"""Check ADR Compliance."""
import pathlib

adr_dir = pathlib.Path('docs/adr')
if adr_dir.exists():
    adrs = sorted(adr_dir.glob('ADR-*.md'))
    issues = []
    for adr in adrs:
        text = adr.read_text().lower()
        if 'open source' not in text and 'free ' not in text:
            issues.append(f'{adr.name}: missing Open Source/Free section')
    for i in issues:
        print(f'  WARNING: {i}')
    print(f'ADR Compliance: {"WARN" if issues else "PASS (" + str(len(adrs)) + " ADRs)"}')
else:
    print('ADR Compliance: SKIP')
