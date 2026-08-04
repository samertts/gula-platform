#!/usr/bin/env python3
"""GULA Execution Kernel — top-level CLI launcher (GULA-KERNEL-001).

Usage:
    python scripts/kernel.py <command>
    python scripts/kernel.py check     # all self-checks (exit 1 on failure)
    python scripts/kernel.py report    # write the three enterprise reports
    python scripts/kernel.py audit     # write KERNEL_AUDIT_REPORT.md
    python scripts/kernel.py --help    # list every command

Every AI Engine depends on the Kernel. The Kernel never performs engineering
work; it provides execution, coordination, resource management, state,
security, knowledge access, checkpointing, and recovery.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.kernel.cli import main

if __name__ == "__main__":
    sys.exit(main())
