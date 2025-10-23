"""ISINMapper service for resolving ISIN codes to ticker symbols."""

import json
from functools import lru_cache
from typing import Any

from app.config import settings


class ISINMapper:
	"""Service to map ISIN codes to ticker symbols using static mapping."""

	def __init__(self):
		"""Initialize the ISIN mapper and load mappings from JSON file."""
		self.mappings: dict[str, dict[str, Any]] = {}
		self._load_mappings()

	def _load_mappings(self) -> None:
		"""Load ISIN to ticker mappings from JSON file."""
		mapping_file = settings.DATA_DIR / "isin_ticker_mapping.json"

		if not mapping_file.exists():
			print(f"Warning: ISIN mapping file not found at {mapping_file}")
			return

		try:
			with open(mapping_file, encoding="utf-8") as f:
				data = json.load(f)
				self.mappings = data.get("mappings", {})
				print(f"Loaded {len(self.mappings)} ISIN mappings")
		except Exception as e:
			print(f"Error loading ISIN mappings: {e}")

	def resolve_isin(self, isin: str) -> str | None:
		"""
		Resolve an ISIN code to a ticker symbol.

		Args:
			isin: The ISIN code to resolve

		Returns:
			The ticker symbol if found, None otherwise
		"""
		if not isin:
			return None

		mapping = self.mappings.get(isin)
		if mapping:
			return mapping.get("ticker")

		return None

	def get_mapping_info(self, isin: str) -> dict[str, Any] | None:
		"""
		Get full mapping information for an ISIN.

		Args:
			isin: The ISIN code

		Returns:
			Dictionary with mapping details or None
		"""
		return self.mappings.get(isin)


@lru_cache
def get_isin_mapper() -> ISINMapper:
	"""Get singleton instance of ISINMapper."""
	return ISINMapper()
