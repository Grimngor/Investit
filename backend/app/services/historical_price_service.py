"""Historical price service for fetching prices on specific dates."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)


class HistoricalPriceService:
	"""Service for fetching historical prices from yfinance."""

	@staticmethod
	async def get_price_on_date(isin: str, date: str) -> dict[str, Any] | None:
		"""
		Fetch the closing price for a fund on a specific date.

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

			# Run yfinance in thread pool
			loop = asyncio.get_event_loop()
			ticker = await loop.run_in_executor(None, yf.Ticker, isin)
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

				logger.info(f"Found historical price for {isin} on {date}: {price} {currency}")

				return {
					"price": price,
					"currency": currency,
					"date": date,
					"exact_match": True,
				}

			# No exact match - use closest date
			# Convert index dates to comparable format
			import pandas as pd

			date_diffs = pd.Series([(hist.index[i].date() - target_date.date()).days for i in range(len(hist.index))])
			closest_idx = date_diffs.abs().argmin()
			closest_row = hist.iloc[closest_idx]
			closest_date = hist.index[closest_idx].date()

			price = float(closest_row["Close"])
			currency = "EUR"

			info = await loop.run_in_executor(None, lambda: ticker.info)
			if "currency" in info:
				currency = info["currency"]

			logger.info(f"No exact match for {isin} on {date}, using {closest_date}: {price} {currency}")

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

			price_data = await HistoricalPriceService.get_price_on_date(isin, date)

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
