"""
Root conftest.py
================
Ensures the project root is on sys.path so that all packages
(dashboard, reports, execution, etc.) are importable in pytest
without requiring a pip install.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
