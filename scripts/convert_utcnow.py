from pathlib import Path

ROOTS = [Path('/home/ubuntu/gula-platform/backend/app'), Path('/home/ubuntu/gula-platform/shared')]
EXCLUDED = {
    Path('/home/ubuntu/gula-platform/backend/app/engineering/repository/generator.py'),
    Path('/home/ubuntu/gula-platform/backend/app/engineering/testing/fixtures.py'),
}
changed = []
for root in ROOTS:
    for path in root.rglob('*.py'):
        if path in EXCLUDED:
            continue
        text = path.read_text()
        if (
            'datetime.utcnow()' not in text
            and 'default_factory=datetime.utcnow' not in text
            and 'default=datetime.utcnow' not in text
            and 'onupdate=datetime.utcnow' not in text
        ):
            continue
        new = text.replace('default_factory=datetime.utcnow', 'default_factory=lambda: datetime.now(UTC)')
        new = new.replace('default=datetime.utcnow', 'default=lambda: datetime.now(UTC)')
        new = new.replace('onupdate=datetime.utcnow', 'onupdate=lambda: datetime.now(UTC)')
        new = new.replace('datetime.utcnow()', 'datetime.now(UTC)')
        new = new.replace('__import__("datetime").datetime.now(UTC)', 'datetime.now(UTC)')
        lines = new.splitlines(keepends=True)
        import_indexes = [i for i, line in enumerate(lines) if line.startswith('from datetime import ')]
        if import_indexes:
            i = import_indexes[0]
            line = lines[i]
            if 'UTC' not in line:
                lines[i] = line.replace('from datetime import ', 'from datetime import UTC, ', 1)
            new = ''.join(lines)
        else:
            # All non-template callsites use the datetime symbol; add a safe top-level import.
            lines = new.splitlines(keepends=True)
            insert_at = 0
            if lines and lines[0].startswith('#!'):
                insert_at = 1
            lines.insert(insert_at, 'from datetime import UTC\n')
            new = ''.join(lines)
        path.write_text(new)
        changed.append(str(path))
print(f'changed={len(changed)}')
for item in changed:
    print(item)
