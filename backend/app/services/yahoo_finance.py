"""Yahoo Finance service for fetching NAV/prices."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)


class YahooFinanceService:
	"""Service for fetching prices from Yahoo Finance using yfinance library."""

	def __init__(self):
		"""Initialize Yahoo Finance service."""
		self.cache: dict[str, dict[str, Any]] = {}
		self.cache_duration = timedelta(hours=24)  # 24-hour cache per PRD

	async def get_quote(self, symbol: str) -> dict[str, Any] | None:
		"""
		Fetch current quote for a symbol using yfinance library.

		Args:
			symbol: Yahoo Finance symbol (e.g., "IE00BYX5NX33.SG")

		Returns:
			Dict with price and metadata, or None if failed
		"""
		# Check cache first
		if symbol in self.cache:
			cached = self.cache[symbol]
			cache_time = datetime.fromisoformat(cached["timestamp"])
			if datetime.now(UTC) - cache_time < self.cache_duration:
				logger.debug(f"Using cached price for {symbol}")
				return cached

		try:
			# Use yfinance library - runs in thread pool since it's blocking I/O
			loop = asyncio.get_event_loop()
			ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
			info = await loop.run_in_executor(None, lambda: ticker.info)

			# Extract price - try multiple fields as Yahoo Finance data varies
			price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("navPrice")

			if price is None:
				logger.warning(f"No price found for {symbol}")
				return None

			# Get the actual Yahoo ticker symbol (yfinance resolves ISIN to ticker)
			actual_symbol = info.get("symbol", symbol)

			quote_data = {
				"symbol": actual_symbol,  # Use resolved ticker, not input ISIN
				"input_symbol": symbol,  # Keep original input for reference
				"price": float(price),
				"currency": info.get("currency", "USD"),
				"timestamp": datetime.now(UTC).isoformat(),
				"exchange": info.get("exchange", ""),
				"name": info.get("longName") or info.get("shortName", ""),
			}

			# Extract fund composition metadata if available
			metadata = self._extract_fund_metadata(info)
			if metadata:
				quote_data.update(metadata)

			# Cache the result
			self.cache[symbol] = quote_data
			logger.info(f"Fetched price for {symbol}: {price} {quote_data['currency']}")

			return quote_data

		except Exception as e:
			logger.warning(f"Could not fetch price for {symbol}: {e!s}")
			return None

	def _extract_fund_metadata(self, info: dict) -> dict[str, Any]:
		"""
		Extract fund composition metadata from Yahoo Finance info.

		Args:
			info: Ticker info dictionary from yfinance

		Returns:
			Dictionary with sector_allocation, geo_allocation, and asset_type if available
		"""
		metadata = {}

		# Determine asset type
		quote_type = info.get("quoteType", "").lower()
		if quote_type in ["etf", "mutualfund"]:
			metadata["asset_type"] = "ETF" if quote_type == "etf" else "Fund"
		elif quote_type == "cryptocurrency":
			metadata["asset_type"] = "Crypto"
		elif quote_type == "equity":
			metadata["asset_type"] = "Stock"

		# Extract sector allocation (for funds/ETFs)
		sector_weightings = info.get("sectorWeightings", [])
		if sector_weightings and isinstance(sector_weightings, list) and len(sector_weightings) > 0:
			# sectorWeightings is a list of dicts like [{"Technology": 0.23}, {"Healthcare": 0.15}]
			sector_allocation = {}
			for sector_dict in sector_weightings:
				if isinstance(sector_dict, dict):
					sector_allocation.update(sector_dict)

			if sector_allocation:
				metadata["sector_allocation"] = sector_allocation

		# Extract geographic allocation
		# Some funds have country weightings
		holdings_by_country = info.get("holdings", {})
		if isinstance(holdings_by_country, dict):
			country_allocation = holdings_by_country.get("countryWeightings", [])
			if country_allocation and isinstance(country_allocation, list):
				geo_allocation = {}
				for country_dict in country_allocation:
					if isinstance(country_dict, dict):
						geo_allocation.update(country_dict)

				if geo_allocation:
					metadata["geo_allocation"] = geo_allocation

		# Alternative: top holdings for geographic inference (less reliable)
		# This is available but would require additional processing

		return metadata

	async def get_multiple_quotes(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
		"""
		Fetch quotes for multiple symbols with rate limiting to avoid HTTP 429.

		Args:
			symbols: List of Yahoo Finance symbols

		Returns:
			Dict mapping symbols to their quote data
		"""
		quotes = {}

		# Process sequentially with delays to avoid rate limiting
		# Yahoo Finance rate limits aggressive requests
		for i, symbol in enumerate(symbols):
			result = await self.get_quote(symbol)
			if isinstance(result, dict):
				quotes[symbol] = result

			# Add delay between requests (except after last one)
			# 0.5 seconds should be safe for Yahoo Finance
			if i < len(symbols) - 1:
				await asyncio.sleep(0.5)

		return quotes

	def is_price_stale(self, timestamp: str, threshold_days: int = 3) -> bool:
		"""
		Check if a cached price is stale.

		Args:
			timestamp: ISO format timestamp
			threshold_days: Number of days to consider stale (default: 3 per PRD)

		Returns:
			True if stale, False otherwise
		"""
		try:
			price_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
			age = datetime.now(UTC) - price_time
			return age.days > threshold_days
		except (ValueError, AttributeError):
			return True

	def clear_cache(self):
		"""Clear the price cache."""
		self.cache.clear()
		logger.info("Yahoo Finance price cache cleared")

	async def get_crypto_quote(self, symbol: str, currency: str = "EUR") -> dict[str, Any] | None:
		"""Fetch current quote for a cryptocurrency using base symbol (e.g., BTC)."""
		from app.utils.validators import get_crypto_yfinance_symbol

		yf_symbol = get_crypto_yfinance_symbol(symbol, currency)
		quote = await self.get_quote(yf_symbol)
		if quote:
			quote["asset_type"] = "Crypto"
		return quote

	async def get_crypto_historical_price(self, symbol: str, date: str, currency: str = "EUR") -> dict[str, Any] | None:
		"""Fetch historical price for a cryptocurrency on a specific date."""
		from app.services.historical_price_service import HistoricalPriceService
		from app.utils.validators import get_crypto_yfinance_symbol

		yf_symbol = get_crypto_yfinance_symbol(symbol, currency)
		return await HistoricalPriceService.get_price_on_date(yf_symbol, date)
