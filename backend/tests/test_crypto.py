"""Tests for cryptocurrency support using yfinance integration."""

import pytest

from app.services.yahoo_finance import YahooFinanceService
from app.utils.validators import get_crypto_yfinance_symbol, is_crypto_symbol


def test_is_crypto_symbol_basic():
	"""Basic detection works for common symbols."""
	assert is_crypto_symbol("BTC") is True
	assert is_crypto_symbol("ETH") is True
	assert is_crypto_symbol("SOL") is True
	assert is_crypto_symbol("DOGE") is True
	# Not crypto
	assert is_crypto_symbol("IE00BYX5NX33") is False
	assert is_crypto_symbol("AAPL") is False  # 4 letters but equity ticker, heuristics treat equities separately later


def test_get_crypto_yfinance_symbol():
	"""Format conversion returns expected pair symbol."""
	assert get_crypto_yfinance_symbol("btc") == "BTC-EUR"
	assert get_crypto_yfinance_symbol("eth", "usd") == "ETH-USD"


@pytest.mark.asyncio
async def test_get_crypto_quote_live():
	"""Fetch a live quote for BTC (may fail if network/Yahoo down)."""
	service = YahooFinanceService()
	quote = await service.get_crypto_quote("BTC")
	assert quote is not None
	assert quote["asset_type"] == "Crypto"
	assert quote["price"] > 0
	assert quote["currency"] in {"EUR", "USD"}


@pytest.mark.asyncio
async def test_get_crypto_historical_price():
	"""Fetch a historical price for BTC on a known past date."""
	service = YahooFinanceService()
	result = await service.get_crypto_historical_price("BTC", "2024-01-10")
	assert result is not None
	assert result["price"] > 0
	assert result["currency"] in {"EUR", "USD"}
