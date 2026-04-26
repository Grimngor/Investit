"""Full pytest runner for pre-push hook."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

def main() -> int:
    """Run full pytest suite."""
    import pytest
    args = ["-q", "--disable-warnings", str(BACKEND / "tests")]  # all backend tests
    return pytest.main(args)

if __name__ == "__main__":
    raise SystemExit(main())
