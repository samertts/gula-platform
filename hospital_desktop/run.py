#!/usr/bin/env python3
"""
NHDW - National Hospital Desktop Workspace
Run script for the PySide6 desktop application.

Usage:
    python run.py [--theme dark|light] [--language ar|en]
                  [--server http://localhost:8000] [--offline]
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()
