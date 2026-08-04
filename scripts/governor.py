#!/usr/bin/env python3
"""GULA Governor — Enterprise AI Governance, Coordination, Safety and Stability Framework.

Mission: GULA-GOVERNOR-001.

Delegates to the `scripts/governor` package. See `python scripts/governor.py --help`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.governor.cli import main

if __name__ == "__main__":
    sys.exit(main())
