"""Application package root."""

from importlib import metadata

try:  # best-effort version discovery if installed as a package
	__version__: str = metadata.version("investit")
except metadata.PackageNotFoundError:  # pragma: no cover - not installed scenario
	__version__ = "0.0.0"

__all__ = ["__version__"]
