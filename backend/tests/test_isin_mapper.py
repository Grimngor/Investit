"""Tests for ISIN resolution and caching."""

from typing import Any

import httpx
import pytest

from app.config import settings
from app.services.isin_mapper import ISINMapper
from app.services.price_service import PriceService
from app.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_isin_resolver_returns_manual_override_without_openfigi(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Manual overrides are returned before provider lookup."""
	StorageService.save_json(
		settings.DATA_DIR / "isin_ticker_mapping.json",
		{"mappings": {"IE00B4L5Y983": {"ticker": "MANUAL.AS", "source": "manual", "manual": True}}},
	)

	async def fail_openfigi(_: ISINMapper, isin: str) -> dict[str, Any] | None:
		raise AssertionError(f"OpenFIGI should not be called for {isin}")

	monkeypatch.setattr(ISINMapper, "_resolve_with_openfigi", fail_openfigi)

	mapper = ISINMapper()

	assert mapper.resolve_isin("IE00B4L5Y983") == "MANUAL.AS"


@pytest.mark.asyncio
async def test_isin_resolver_calls_openfigi_and_reuses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
	"""OpenFIGI results are normalized, persisted, and reused from cache."""
	calls = []

	class FakeResponse:
		status_code = 200

		def raise_for_status(self) -> None:
			return None

		def json(self) -> list[dict[str, Any]]:
			return [
				{
					"data": [
						{
							"ticker": "IWDA",
							"exchCode": "AS",
							"name": "iShares Core MSCI World",
							"currency": "EUR",
							"figi": "BBG000TEST",
						}
					]
				}
			]

	class FakeClient:
		def __init__(self, *args: Any, **kwargs: Any) -> None:
			return None

		async def __aenter__(self) -> "FakeClient":
			return self

		async def __aexit__(self, *args: Any) -> None:
			return None

		async def post(self, url: str, headers: dict[str, str], json: list[dict[str, str]]) -> FakeResponse:
			calls.append((url, headers, json))
			return FakeResponse()

	monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

	mapper = ISINMapper()
	first = await mapper.resolve_isin_info("IE00B4L5Y983")
	second = await mapper.resolve_isin_info("IE00B4L5Y983")

	assert first is not None
	assert first["ticker"] == "IWDA.AS"
	assert second is not None
	assert second["ticker"] == "IWDA.AS"
	assert len(calls) == 1
	cache = StorageService.load_json(settings.DATA_DIR / "isin_resolution_cache.json", default={})
	assert cache["mappings"]["IE00B4L5Y983"]["source"] == "openfigi"


@pytest.mark.asyncio
async def test_isin_resolver_handles_openfigi_errors(monkeypatch: pytest.MonkeyPatch) -> None:
	"""OpenFIGI failures return None instead of raising."""

	class FakeClient:
		def __init__(self, *args: Any, **kwargs: Any) -> None:
			return None

		async def __aenter__(self) -> "FakeClient":
			return self

		async def __aexit__(self, *args: Any) -> None:
			return None

		async def post(self, *args: Any, **kwargs: Any) -> httpx.Response:
			raise httpx.ConnectError("offline")

	monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

	assert await ISINMapper().resolve_isin_info("IE00UNKNOWN0") is None


@pytest.mark.asyncio
async def test_price_service_uses_resolved_symbol_before_suffix_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Traditional quote fetching tries the resolved ISIN symbol before suffix fallbacks."""
	from app.services.isin_mapper import get_isin_mapper
	from app.services.morningstar_service import MorningstarService
	from app.services.yahoo_finance import YahooFinanceService

	get_isin_mapper.cache_clear()
	StorageService.save_json(
		settings.DATA_DIR / "isin_ticker_mapping.json",
		{"mappings": {"IE00B4L5Y983": {"ticker": "IWDA.AS", "source": "manual", "manual": True}}},
	)
	calls = []

	async def fake_get_quote(self: YahooFinanceService, symbol: str) -> dict[str, Any] | None:
		calls.append(symbol)
		if symbol == "IWDA.AS":
			return {"price": 100.0, "currency": "EUR", "timestamp": "2026-01-01T00:00:00+00:00", "symbol": symbol, "name": "IWDA"}
		return None

	async def no_morningstar(self: MorningstarService, isin: str) -> dict[str, Any] | None:
		return None

	async def no_yahoo_metadata(self: YahooFinanceService, symbol: str) -> dict[str, Any] | None:
		return None

	monkeypatch.setattr(YahooFinanceService, "get_quote", fake_get_quote)
	monkeypatch.setattr(MorningstarService, "get_fund_metadata", no_morningstar)
	monkeypatch.setattr(YahooFinanceService, "get_fund_metadata", no_yahoo_metadata)

	quote = await PriceService.fetch_traditional_quote("IE00B4L5Y983")

	assert quote is not None
	assert quote["symbol"] == "IWDA.AS"
	assert calls == ["IWDA.AS"]
