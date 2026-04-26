"""Fast failing pytest runner for pre-commit."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

def main() -> int:
    """Run a quick pytest with fail-fast settings."""
    import pytest

    args = ["-q", "--maxfail=1", "--disable-warnings", str(BACKEND / "tests")]  # limit scope to backend tests
    return pytest.main(args)

if __name__ == "__main__":
    raise SystemExit(main())
