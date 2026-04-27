"""Fast failing pytest runner for pre-commit."""
from __future__ import annotations
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
TEST_DATA_DIR = ROOT / ".cache" / "pytest" / "pre-commit-data"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

def main() -> int:
	"""Run a quick pytest with fail-fast settings."""
	shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
	TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
	os.environ["DATA_DIR"] = str(TEST_DATA_DIR)

	import pytest

	args = ["-q", "--maxfail=1", "--disable-warnings", str(BACKEND / "tests")]  # limit scope to backend tests
	return pytest.main(args)

if __name__ == "__main__":
    raise SystemExit(main())
