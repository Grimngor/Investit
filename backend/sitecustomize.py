"""Test runner path adjustments.

Ensures 'app' package is importable when invoking pytest directly without
manually exporting PYTHONPATH. Python automatically imports sitecustomize
if present on sys.path early during startup.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
if str(BACKEND) not in sys.path:
	sys.path.insert(0, str(BACKEND))
