"""Provider fallback ordering, source attribution, and health recording."""

from datetime import UTC, datetime
from typing import Any

from app.services.metrics_service import metrics

PRICE_PROVIDER_ORDER = ("yahoo_finance.quote", "stale_cache")
METADATA_PROVIDER_ORDER = ("yahoo_finance.quote", "morningstar", "yahooquery", "existing_metadata")
ISIN_PROVIDER_ORDER = ("manual_override", "fresh_cache", "openfigi", "stale_cache", "static_mapping")


class ProviderReliabilityService:
	"""Centralize provider reliability behavior for market-data flows."""

	@staticmethod
	def provider_order(operation: str) -> tuple[str, ...]:
		"""Return the explicit provider fallback order for an operation."""
		orders = {
			"price": PRICE_PROVIDER_ORDER,
			"metadata": METADATA_PROVIDER_ORDER,
			"isin": ISIN_PROVIDER_ORDER,
		}
		return orders.get(operation, ())

	@staticmethod
	def record_attempt(provider: str, operation: str, success: bool, detail: str | None = None) -> None:
		"""Record provider health for one operation attempt."""
		metrics.record_provider_call(provider, operation, success, detail=detail)

	@staticmethod
	def annotate(
		data: dict[str, Any],
		source: str,
		operation: str,
		provider_attempts: list[dict[str, Any]] | None = None,
		detail: str | None = None,
	) -> dict[str, Any]:
		"""Attach normalized source attribution to provider-derived data."""
		attributed = dict(data)
		attributed["source"] = source
		attributed["source_operation"] = operation
		attributed["source_detail"] = detail or source
		if provider_attempts is not None:
			attributed["provider_attempts"] = provider_attempts
		return attributed

	@staticmethod
	def attempt(provider: str, success: bool, detail: str | None = None) -> dict[str, Any]:
		"""Build a serializable provider attempt record."""
		return {
			"provider": provider,
			"success": success,
			"detail": detail,
			"timestamp": datetime.now(UTC).isoformat(),
		}
