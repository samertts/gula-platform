"""Fix `from datetime import UTC` → `from app._compat import UTC` for Python 3.10 compat.

Usage: python3 scripts/fix_datetime_utc.py backend/app/
"""

import re
import sys
from pathlib import Path


def fix_file(filepath: Path) -> bool:
    content = filepath.read_text()
    original = content

    # Pattern 1: `from datetime import UTC, datetime, timedelta`
    # Pattern 2: `from datetime import datetime, timedelta, UTC` (any order)
    # Pattern 3: `from datetime import UTC`
    # Pattern 4: `from datetime import UTC, date, datetime`
    # etc.

    # Replace `from datetime import UTC` or `from datetime import UTC, ...`
    # by removing UTC from the import and adding a separate compat import

    lines = content.split("\n")
    new_lines = []
    changed = False

    for line in lines:
        m = re.match(r"^from datetime import (.*)$", line)
        if m:
            imports = [x.strip() for x in m.group(1).split(",")]
            if "UTC" in imports:
                imports.remove("UTC")
                changed = True
                if imports:
                    # Keep the remaining datetime imports
                    new_lines.append(f"from datetime import {', '.join(imports)}")
                # Add compat import
                new_lines.append("from app._compat import UTC")
                continue
        new_lines.append(line)

    if changed:
        filepath.write_text("\n".join(new_lines))

    return changed


def main(root: str) -> None:
    root_path = Path(root)
    if not root_path.is_dir():
        print(f"Error: {root} is not a directory")
        sys.exit(1)

    files = list(root_path.rglob("*.py"))
    fixed = 0
    for fpath in sorted(files):
        if fix_file(fpath):
            print(f"  Fixed: {fpath.relative_to(root_path.parent)}")
            fixed += 1

    print(f"\nFixed {fixed} file(s)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fix_datetime_utc.py <directory>")
        sys.exit(1)
    main(sys.argv[1])
