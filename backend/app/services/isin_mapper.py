"""ISINMapper service for resolving ISIN codes to ticker symbols."""

import logging
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

import httpx

from app.config import settings
from app.services.provider_reliability import ProviderReliabilityService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

OPENFIGI_MAPPING_URL = "https://api.openfigi.com/v3/mapping"


class ISINMapper:
	"""Service to map ISIN codes to ticker symbols using overrides, cache, and OpenFIGI."""

	def __init__(self) -> None:
		"""Initialize the ISIN mapper and load mappings from JSON files."""
		self.overrides: dict[str, dict[str, Any]] = {}
		self.cache: dict[str, dict[str, Any]] = {}
		self._load_mappings()
		self._load_cache()

	def _load_mappings(self) -> None:
		"""Load manual/static ISIN to ticker mappings from JSON file."""
		mapping_file = settings.DATA_DIR / "isin_ticker_mapping.json"
		data = StorageService.load_json(mapping_file, default={"mappings": {}})
		self.overrides = data.get("mappings", {}) if isinstance(data, dict) else {}

	def _load_cache(self) -> None:
		"""Load provider-derived ISIN resolution cache."""
		cache_file = settings.DATA_DIR / "isin_resolution_cache.json"
		data = StorageService.load_json(cache_file, default={"mappings": {}})
		self.cache = data.get("mappings", {}) if isinstance(data, dict) else {}

	def _save_cache(self) -> None:
		"""Persist provider-derived ISIN resolution cache."""
		cache_file = settings.DATA_DIR / "isin_resolution_cache.json"
		StorageService.save_json(cache_file, {"mappings": self.cache})

	def _is_fresh(self, mapping: dict[str, Any]) -> bool:
		"""Return True when a cached mapping is within the configured freshness window."""
		timestamp = mapping.get("timestamp")
		if not timestamp:
			return False
		try:
			cache_time = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
		except ValueError:
			return False
		return datetime.now(UTC) - cache_time < timedelta(days=settings.ISIN_RESOLUTION_CACHE_DAYS)

	def _manual_override(self, isin: str) -> dict[str, Any] | None:
		"""Return an explicit manual override for an ISIN when one exists."""
		mapping = self.overrides.get(isin)
		if not mapping:
			return None
		if mapping.get("manual") is True or mapping.get("source") == "manual":
			return {**mapping, "isin": isin, "source": mapping.get("source", "manual")}
		return None

	def _static_fallback(self, isin: str) -> dict[str, Any] | None:
		"""Return a non-manual local mapping as a final fallback."""
		mapping = self.overrides.get(isin)
		if not mapping:
			return None
		return {**mapping, "isin": isin, "source": mapping.get("source", "local")}

	def _normalize_openfigi_result(self, isin: str, result: dict[str, Any]) -> dict[str, Any] | None:
		"""Normalize the first OpenFIGI result into the local mapping shape."""
		ticker = result.get("ticker")
		if not ticker:
			return None
		exch_code = result.get("exchCode")
		symbol = f"{ticker}.{exch_code}" if exch_code and "." not in ticker else ticker
		return {
			"isin": isin,
			"ticker": symbol,
			"name": result.get("name"),
			"exchange": exch_code,
			"currency": result.get("currency"),
			"figi": result.get("figi"),
			"composite_figi": result.get("compositeFIGI"),
			"source": "openfigi",
			"timestamp": datetime.now(UTC).isoformat(),
		}

	async def _resolve_with_openfigi(self, isin: str) -> dict[str, Any] | None:
		"""Resolve an ISIN through OpenFIGI."""
		headers = {"Content-Type": "application/json"}
		if settings.OPENFIGI_API_KEY:
			headers["X-OPENFIGI-APIKEY"] = settings.OPENFIGI_API_KEY

		try:
			async with httpx.AsyncClient(timeout=10.0) as client:
				response = await client.post(OPENFIGI_MAPPING_URL, headers=headers, json=[{"idType": "ID_ISIN", "idValue": isin}])
			if response.status_code == 429:
				logger.warning(f"OpenFIGI rate limit reached while resolving {isin}")
				ProviderReliabilityService.record_attempt("openfigi", "isin", False, f"{isin}: rate limited")
				return None
			response.raise_for_status()
			payload = response.json()
		except (httpx.HTTPError, ValueError) as e:
			logger.warning(f"Could not resolve {isin} with OpenFIGI: {e!s}")
			ProviderReliabilityService.record_attempt("openfigi", "isin", False, f"{isin}: {e!s}")
			return None

		if not isinstance(payload, list) or not payload:
			return None
		data = payload[0].get("data") if isinstance(payload[0], dict) else None
		if not data:
			return None
		for result in data:
			if isinstance(result, dict):
				normalized = self._normalize_openfigi_result(isin, result)
				if normalized:
					self.cache[isin] = normalized
					self._save_cache()
					ProviderReliabilityService.record_attempt("openfigi", "isin", True, isin)
					return normalized
		ProviderReliabilityService.record_attempt("openfigi", "isin", False, f"{isin}: no mapping")
		return None

	async def resolve_isin_info(self, isin: str) -> dict[str, Any] | None:
		"""Resolve an ISIN code to ticker metadata."""
		if not isin:
			return None

		isin = isin.upper()
		mapping: dict[str, Any] | None = None
		source = ""
		detail = ""
		manual = self._manual_override(isin)
		if manual:
			mapping = manual
			source = "manual_override"
			detail = "Manual ISIN mapping"
		else:
			cached = self.cache.get(isin)
			if cached and self._is_fresh(cached):
				mapping = cached
				source = "fresh_cache"
				detail = "Fresh ISIN resolution cache"
			else:
				openfigi = await self._resolve_with_openfigi(isin)
				if openfigi:
					mapping = openfigi
					source = "openfigi"
					detail = "OpenFIGI ISIN mapping"
				elif cached:
					mapping = cached
					source = "stale_cache"
					detail = "Stale ISIN resolution cache"
				else:
					mapping = self._static_fallback(isin)
					source = "static_mapping" if mapping else ""
					detail = "Static ISIN mapping"

		if not mapping:
			return None
		if source != "openfigi":
			ProviderReliabilityService.record_attempt(source, "isin", True, isin)
		return ProviderReliabilityService.annotate(mapping, source, "isin", detail=detail)

	def resolve_isin(self, isin: str) -> str | None:
		"""Resolve an ISIN code to a locally available ticker symbol."""
		if not isin:
			return None
		isin = isin.upper()
		mapping = self._manual_override(isin) or self.cache.get(isin) or self._static_fallback(isin)
		if mapping:
			return mapping.get("ticker")
		return None

	def get_mapping_info(self, isin: str) -> dict[str, Any] | None:
		"""Get locally loaded mapping information for an ISIN."""
		return self.overrides.get(isin) or self.cache.get(isin)


@lru_cache
def get_isin_mapper() -> ISINMapper:
	"""Get singleton instance of ISINMapper."""
	return ISINMapper()
