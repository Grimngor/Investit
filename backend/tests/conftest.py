"""Pytest configuration: path setup and warning filters."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

# Ensure backend path is on sys.path for 'app' package imports when running pytest directly.
BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
	sys.path.insert(0, str(BACKEND))

# Silence deprecation warning from python-jose using utcnow (third-party)
warnings.filterwarnings(
	"ignore",
	category=DeprecationWarning,
	message=r".*datetime\.utcnow\(\) is deprecated.*",
)

# Additional global fixtures can be added here.
