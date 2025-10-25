"""Morningstar service for accurate fund geographic and sector allocations."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import mstarpy

logger = logging.getLogger(__name__)


class MorningstarService:
	"""Service for fetching fund metadata from Morningstar using mstarpy."""

	def __init__(self):
		"""Initialize Morningstar service with cache."""
		self.cache: dict[str, dict[str, Any]] = {}
		self.cache_duration = timedelta(days=30)

	async def get_fund_metadata(self, isin: str) -> dict[str, Any] | None:
		"""
		Fetch comprehensive fund metadata from Morningstar.

		Args:
			isin: Fund ISIN code (e.g., "IE00BYX5NX33")

		Returns:
			Dictionary with regional_allocation, sector_allocation, and fund info
		"""
		# Check cache
		if isin in self.cache:
			cached = self.cache[isin]
			cache_time = datetime.fromisoformat(cached["timestamp"])
			if datetime.now(UTC) - cache_time < self.cache_duration:
				logger.debug(f"Using cached Morningstar data for {isin}")
				return cached

		try:
			# Run mstarpy in thread pool (blocking I/O)
			loop = asyncio.get_event_loop()
			fund = await loop.run_in_executor(None, lambda: mstarpy.Funds(isin, language="en-gb"))

			# Check if fund was found
			if not fund.name or fund.name == "":
				logger.warning(f"Fund not found in Morningstar: {isin}")
				return None

			logger.info(f"Morningstar: Found fund {fund.name} for {isin}")

			metadata: dict[str, Any] = {
				"name": fund.name,
				"isin": fund.isin,
				"morningstar_code": fund.code,
				"timestamp": datetime.now(UTC).isoformat(),
				"source": "morningstar",
			}

			# Get regional breakdown
			logger.debug(f"Fetching regional data for {isin}")
			regional_data = await loop.run_in_executor(None, fund.regionalSector)

			if regional_data and "fundPortfolio" in regional_data:
				portfolio = regional_data["fundPortfolio"]
				logger.debug(f"Regional portfolio data: {portfolio}")
				# Extract regional percentages
				regional_allocation = {}

				# Map Morningstar region names to cleaner display names
				region_map = {
					"northAmerica": "North America",
					"europeDeveloped": "Europe (Developed)",
					"europeEmerging": "Europe (Emerging)",
					"unitedKingdom": "United Kingdom",
					"japan": "Japan",
					"australasia": "Australasia",
					"asiaDeveloped": "Asia (Developed)",
					"asiaEmerging": "Asia (Emerging)",
					"africaMiddleEast": "Africa/Middle East",
					"latinAmerica": "Latin America",
				}

				for mstar_key, display_name in region_map.items():
					if mstar_key in portfolio and portfolio[mstar_key] > 0:
						# Convert to decimal (Morningstar returns percentages)
						regional_allocation[display_name] = portfolio[mstar_key] / 100.0

				if regional_allocation:
					metadata["regional_allocation"] = regional_allocation
					logger.info(f"Morningstar: Got {len(regional_allocation)} regions for {isin}")
				else:
					logger.warning(f"Morningstar: No regional data found for {isin}")

			# Get sector breakdown (same as what we get from yahooquery, but from Morningstar)
			logger.debug(f"Fetching sector data for {isin}")
			sector_data = await loop.run_in_executor(None, fund.sector)
			if sector_data and "EQUITY" in sector_data:
				equity_sectors = sector_data["EQUITY"].get("fundPortfolio", {})

				# Map to clean sector names
				sector_map = {
					"basicMaterials": "Basic Materials",
					"consumerCyclical": "Consumer Cyclical",
					"financialServices": "Financial Services",
					"realEstate": "Real Estate",
					"communicationServices": "Communication Services",
					"energy": "Energy",
					"industrials": "Industrials",
					"technology": "Technology",
					"consumerDefensive": "Consumer Defensive",
					"healthcare": "Healthcare",
					"utilities": "Utilities",
				}

				sector_allocation = {}
				for mstar_key, display_name in sector_map.items():
					if mstar_key in equity_sectors and equity_sectors[mstar_key] > 0:
						# Convert to decimal
						sector_allocation[display_name] = equity_sectors[mstar_key] / 100.0

				if sector_allocation:
					metadata["sector_allocation"] = sector_allocation

			# Cache and return
			self.cache[isin] = metadata
			logger.info(f"Fetched Morningstar metadata for {isin}: {fund.name}")

			return metadata

		except Exception as e:
			logger.warning(f"Could not fetch Morningstar data for {isin}: {e!s}")
			return None

	def clear_cache(self):
		"""Clear the metadata cache."""
		self.cache.clear()
		logger.info("Morningstar metadata cache cleared")
