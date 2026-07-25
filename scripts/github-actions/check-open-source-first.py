#!/usr/bin/env python3
"""Check Open Source First compliance."""
import pathlib

proprietary = ['commercial', 'proprietary', 'all rights reserved', 'eula', 'enterprise license']
issues = []
for f in list(pathlib.Path('.').rglob('requirements*.txt')) + list(pathlib.Path('.').rglob('package.json')):
    if 'node_modules' in str(f):
        continue
    text = f.read_text().lower()
    for lic in proprietary:
        if lic in text:
            issues.append(f'{f}: contains "{lic}"')

if issues:
    for i in issues:
        print(f'  WARNING: {i}')
    print('Open Source First: WARN')
else:
    print('Open Source First: PASS')
