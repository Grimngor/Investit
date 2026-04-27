"""Yahoo Finance service for fetching NAV/prices."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf
from yahooquery import Ticker

from app.config import settings
from app.utils.retry import async_retry
from app.utils.validators import get_crypto_yfinance_symbol, is_crypto_symbol, validate_price

logger = logging.getLogger(__name__)


class YahooFinanceService:
	"""Service for fetching prices from Yahoo Finance using yfinance library."""

	# Exchange suffix -> ISO country code (used for geo inference)
	_EXCHANGE_COUNTRY_MAP: dict[str, str] = {
		"L": "GB",  # London
		"PA": "FR",  # Paris
		"DE": "DE",  # Germany
		"SW": "CH",  # Switzerland
		"AS": "NL",  # Amsterdam
		"MI": "IT",  # Milan
		"HK": "HK",  # Hong Kong
		"T": "JP",  # Tokyo
		"AX": "AU",  # Australia
	}

	def __init__(self):
		"""Initialize Yahoo Finance service."""
		self.cache: dict[str, dict[str, Any]] = {}
		self.cache_duration = timedelta(hours=settings.PRICE_CACHE_HOURS)
		self.metadata_cache: dict[str, dict[str, Any]] = {}
		self.metadata_cache_duration = timedelta(days=settings.METADATA_CACHE_DAYS)

	@async_retry(retries=3, base_delay=1.0, exceptions=(Exception,))
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

			if price is None or not validate_price(price):
				logger.warning(f"No valid price found for {symbol}: {price}")
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
					metadata["country_allocation"] = geo_allocation

		# Alternative: top holdings for geographic inference (less reliable)
		# This is available but would require additional processing

		return metadata

	@async_retry(retries=2, base_delay=2.0, exceptions=(Exception,))
	async def get_fund_metadata(self, symbol: str) -> dict[str, Any] | None:
		"""
		Fetch comprehensive fund metadata including sector weightings and holdings via yahooquery.

		Args:
			symbol: Yahoo Finance ticker symbol (e.g., "0P0001CLDK.F")

		Returns:
			Dictionary with sector_allocation, top_holdings, asset_type, price, etc.
		"""
		# Check cache first
		if symbol in self.metadata_cache:
			cached = self.metadata_cache[symbol]
			cache_time = datetime.fromisoformat(cached["timestamp"])
			if datetime.now(UTC) - cache_time < self.metadata_cache_duration:
				logger.debug(f"Using cached fund metadata for {symbol}")
				return cached

		try:
			# Run yahooquery in thread pool since it's blocking
			loop = asyncio.get_event_loop()
			ticker = await loop.run_in_executor(None, Ticker, symbol)

			# Fetch multiple modules in parallel via yahooquery
			fund_data: dict[str, Any] = {}

			# 1. Price info
			price_info = await loop.run_in_executor(None, lambda: ticker.price)
			if symbol in price_info and isinstance(price_info[symbol], dict):
				price_data = price_info[symbol]
				fund_data["price"] = price_data.get("regularMarketPrice")
				fund_data["currency"] = price_data.get("currency", "USD")
				fund_data["exchange"] = price_data.get("exchange", "")
				fund_data["asset_type"] = self._map_quote_type(price_data.get("quoteType"))

			# 2. Sector weightings
			sector_weights = await loop.run_in_executor(None, lambda: ticker.fund_sector_weightings)
			# yahooquery returns a DataFrame for sector weightings
			if hasattr(sector_weights, "to_dict") and not sector_weights.empty:
				# Convert DataFrame to dict - get the column for our symbol
				sector_dict = sector_weights[symbol].to_dict() if symbol in sector_weights.columns else {}
				if sector_dict:
					fund_data["sector_allocation"] = self._normalize_sector_keys(sector_dict)

			# 3. Fund holding info (includes top holdings + position breakdown)
			holding_info = await loop.run_in_executor(None, lambda: ticker.fund_holding_info)
			if symbol in holding_info and isinstance(holding_info[symbol], dict):
				holdings_data = holding_info[symbol]

				# Extract top holdings for reference
				if "holdings" in holdings_data:
					fund_data["top_holdings"] = holdings_data["holdings"][:10]  # Top 10

				# Asset class breakdown
				fund_data["stock_position"] = holdings_data.get("stockPosition", 0.0)
				fund_data["bond_position"] = holdings_data.get("bondPosition", 0.0)
				fund_data["cash_position"] = holdings_data.get("cashPosition", 0.0)

			# 4. Fund profile (name, family, etc.)
			profile = await loop.run_in_executor(None, lambda: ticker.fund_profile)
			if symbol in profile and isinstance(profile[symbol], dict):
				profile_data = profile[symbol]
				fund_data["name"] = profile_data.get("family", "")
				fund_data["fund_family"] = profile_data.get("family", "")

			# 5. Try to infer geography from top holdings (best effort)
			if "top_holdings" in fund_data:
				geo_allocation = self._infer_geography_from_holdings(fund_data["top_holdings"])
				if geo_allocation:
					fund_data["country_allocation"] = geo_allocation

			if not fund_data:
				logger.warning(f"No fund metadata found for {symbol}")
				return None

			# Add timestamp and cache
			fund_data["symbol"] = symbol
			fund_data["timestamp"] = datetime.now(UTC).isoformat()
			fund_data["source"] = "yahooquery"

			self.metadata_cache[symbol] = fund_data
			logger.info(f"Fetched fund metadata for {symbol}: {len(fund_data)} fields")

			return fund_data

		except Exception as e:
			logger.warning(f"Could not fetch fund metadata for {symbol}: {e!s}")
			return None

	def _map_quote_type(self, quote_type: str | None) -> str:
		"""Map Yahoo quote type to our asset_type taxonomy."""
		if not quote_type:
			return "Fund"
		qt = quote_type.lower()
		if qt == "mutualfund":
			return "Fund"
		if qt == "etf":
			return "ETF"
		if qt == "cryptocurrency":
			return "Crypto"
		if qt == "equity":
			return "Stock"
		return "Fund"

	def _normalize_sector_keys(self, sector_dict: dict[str, float]) -> dict[str, float]:
		"""Normalize yahooquery sector keys to readable names."""
		name_map = {
			"technology": "Technology",
			"financial_services": "Financial Services",
			"healthcare": "Healthcare",
			"consumer_cyclical": "Consumer Cyclical",
			"consumer_defensive": "Consumer Defensive",
			"industrials": "Industrials",
			"communication_services": "Communication Services",
			"energy": "Energy",
			"utilities": "Utilities",
			"realestate": "Real Estate",
			"real_estate": "Real Estate",
			"basic_materials": "Basic Materials",
		}
		normalized = {}
		for key, value in sector_dict.items():
			clean_key = name_map.get(key.lower(), key.replace("_", " ").title())
			normalized[clean_key] = float(value)
		return normalized

	def _infer_geography_from_holdings(self, holdings: list[dict[str, Any]]) -> dict[str, float] | None:
		"""
		Infer geographic allocation from top holdings symbols.
		"""
		MIN_COVERAGE_THRESHOLD = 0.1  # 10% minimum coverage to return geography data
		geography_map: dict[str, float] = {}
		total_weight = 0.0

		for holding in holdings:
			symbol = holding.get("symbol", "")
			weight = holding.get("holdingPercent", 0.0)

			if not symbol or not weight:
				continue

			# Infer country from symbol suffix or name
			country = "US"  # Default assumption for major funds
			if "." in symbol:
				suffix = symbol.split(".")[-1]
				country = self._EXCHANGE_COUNTRY_MAP.get(suffix, "US")

			geography_map[country] = geography_map.get(country, 0.0) + weight
			total_weight += weight

		if total_weight < MIN_COVERAGE_THRESHOLD:
			return None

		return geography_map

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

	def is_price_stale(self, timestamp: str, threshold_days: int | None = None) -> bool:
		"""
		Check if a cached price is stale.

		Args:
			timestamp: ISO format timestamp
			threshold_days: Override number of days (defaults to settings.PRICE_STALE_THRESHOLD_DAYS)

		Returns:
			True if stale, False otherwise
		"""
		if threshold_days is None:
			threshold_days = settings.PRICE_STALE_THRESHOLD_DAYS
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
		yf_symbol = get_crypto_yfinance_symbol(symbol, currency)
		quote = await self.get_quote(yf_symbol)
		if quote:
			quote["asset_type"] = "Crypto"
		return quote

	async def get_crypto_historical_price(self, symbol: str, date: str, currency: str = "EUR") -> dict[str, Any] | None:
		"""Fetch historical price for a cryptocurrency on a specific date."""
		yf_symbol = get_crypto_yfinance_symbol(symbol, currency)
		return await self.get_price_on_date(yf_symbol, date)

	@staticmethod
	async def get_price_on_date(isin: str, date: str) -> dict[str, Any] | None:
		"""
		Fetch the closing price for an instrument (fund/stock/crypto) on a specific date.

		Args:
			isin: Fund ISIN code
			date: Date string in format "YYYY-MM-DD"

		Returns:
			Dict with price, currency, date, or None if not found
		"""
		try:
			# Parse the date
			target_date = datetime.strptime(date, "%Y-%m-%d")

			# Fetch historical data (1 week window to handle weekends/holidays)
			start_date = target_date - timedelta(days=3)
			end_date = target_date + timedelta(days=3)

			# Normalize symbol: if looks like crypto base symbol (BTC) convert to BTC-EUR
			resolved_symbol = get_crypto_yfinance_symbol(isin, "EUR") if is_crypto_symbol(isin) else isin

			# Run yfinance in thread pool
			loop = asyncio.get_event_loop()
			ticker = await loop.run_in_executor(None, yf.Ticker, resolved_symbol)
			hist = await loop.run_in_executor(
				None,
				lambda: ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d")),
			)

			if hist.empty:
				logger.warning(f"No historical data found for {isin} around {date}")
				return None

			# Try to find exact date first
			hist.index = hist.index.tz_localize(None)  # Remove timezone for comparison
			matching_rows = hist[hist.index.date == target_date.date()]

			if not matching_rows.empty:
				# Found exact date
				price = float(matching_rows["Close"].values[0])
				currency = "EUR"  # Most European funds are EUR

				# Try to get currency from ticker info
				info = await loop.run_in_executor(None, lambda: ticker.info)
				if "currency" in info:
					currency = info["currency"]

				logger.info(f"Found historical price for {resolved_symbol} on {date}: {price} {currency}")

				return {
					"price": price,
					"currency": currency,
					"date": date,
					"exact_match": True,
				}

			# No exact match - use closest date
			# Convert index dates to comparable format

			date_diffs = pd.Series([(hist.index[i].date() - target_date.date()).days for i in range(len(hist.index))])
			closest_idx = date_diffs.abs().argmin()
			closest_row = hist.iloc[closest_idx]
			closest_date = hist.index[closest_idx].date()

			price = float(closest_row["Close"])
			currency = "EUR"

			info = await loop.run_in_executor(None, lambda: ticker.info)
			if "currency" in info:
				currency = info["currency"]

			logger.info(f"No exact match for {resolved_symbol} on {date}, using {closest_date}: {price} {currency}")

			return {
				"price": price,
				"currency": currency,
				"date": str(closest_date),
				"requested_date": date,
				"exact_match": False,
			}

		except Exception as e:
			logger.error(f"Error fetching historical price for {isin} on {date}: {e}")
			return None

	@staticmethod
	async def backfill_order_prices(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
		"""
		Backfill price_per_share for orders missing this field.

		Args:
			orders: List of order dictionaries

		Returns:
			Updated list of orders with price_per_share filled
		"""
		updated_orders = []

		for order in orders:
			# Skip if already has price_per_share
			if "price_per_share" in order and order["price_per_share"] is not None:
				updated_orders.append(order)
				continue

			# Skip if missing required fields
			if not all(key in order for key in ["isin", "date", "amount_eur", "shares"]):
				updated_orders.append(order)
				continue

			# Skip if shares is 0 (would cause division by zero)
			if order["shares"] == 0:
				updated_orders.append(order)
				continue

			# Fetch historical price
			isin = order["isin"]
			date = order["date"]

			price_data = await YahooFinanceService.get_price_on_date(isin, date)

			if price_data:
				order["price_per_share"] = price_data["price"]
				order["price_currency"] = price_data["currency"]
				order["price_date"] = price_data["date"]
				logger.info(f"Backfilled price for order {order.get('id', 'unknown')}: " f"{price_data['price']} {price_data['currency']}")
			else:
				# Fallback to calculated price from amount/shares
				calculated_price = order["amount_eur"] / order["shares"]
				order["price_per_share"] = calculated_price
				order["price_currency"] = "EUR"
				order["price_date"] = date
				logger.warning(f"Could not fetch historical price for {isin} on {date}, " f"using calculated: {calculated_price:.4f} EUR")

			updated_orders.append(order)

		return updated_orders
