"""Yahoo Query service for comprehensive fund metadata (sector/holdings/geographic data)."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from yahooquery import Ticker

logger = logging.getLogger(__name__)


class YahooQueryService:
	"""Service for fetching detailed fund metadata using yahooquery library."""

	def __init__(self):
		"""Initialize Yahoo Query service with cache."""
		self.cache: dict[str, dict[str, Any]] = {}
		self.cache_duration = timedelta(days=30)  # Fund metadata changes monthly

	async def get_fund_metadata(self, symbol: str) -> dict[str, Any] | None:
		"""
		Fetch comprehensive fund metadata including sector weightings and holdings.

		Args:
			symbol: Yahoo Finance ticker symbol (e.g., "0P0001CLDK.F")

		Returns:
			Dictionary with sector_allocation, top_holdings, asset_type, price, etc.
		"""
		# Check cache first
		if symbol in self.cache:
			cached = self.cache[symbol]
			cache_time = datetime.fromisoformat(cached["timestamp"])
			if datetime.now(UTC) - cache_time < self.cache_duration:
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

			# 2. Sector weightings (critical!)
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
					fund_data["geo_allocation"] = geo_allocation

			if not fund_data:
				logger.warning(f"No fund metadata found for {symbol}")
				return None

			# Add timestamp and cache
			fund_data["symbol"] = symbol
			fund_data["timestamp"] = datetime.now(UTC).isoformat()
			fund_data["source"] = "yahooquery"

			self.cache[symbol] = fund_data
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
		# yahooquery uses keys like "technology", "financial_services", etc.
		# Map to clean display names
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

		This is a best-effort heuristic - for more accuracy, users should
		manually override with factsheet data.

		Args:
			holdings: List of top holdings with symbol/name

		Returns:
			Dict mapping country codes to estimated percentages, or None
		"""
		# Symbol suffix heuristics (not perfect, but useful)
		# .L = London (UK), .PA = Paris (FR), .DE = Germany, .SW = Swiss, etc.
		# US tickers typically have no suffix

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
				suffix_map = {
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
				country = suffix_map.get(suffix, "US")

			geography_map[country] = geography_map.get(country, 0.0) + weight
			total_weight += weight

		# Only return if we have reasonable coverage (>10% of fund)
		if total_weight < MIN_COVERAGE_THRESHOLD:
			return None

		return geography_map

	def clear_cache(self):
		"""Clear the metadata cache."""
		self.cache.clear()
		logger.info("YahooQuery metadata cache cleared")
