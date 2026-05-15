"""Compute service for portfolio calculations (PnL, positions, metrics)."""

from datetime import datetime
from decimal import Decimal
from typing import Any


class ComputeService:
	"""Service for portfolio computations and financial calculations."""

	OTHER_ALLOCATION_LABEL = "Others"
	COUNTRY_NAMES = {
		"US": "United States",
		"CA": "Canada",
		"AE": "United Arab Emirates",
		"GB": "United Kingdom",
		"DE": "Germany",
		"FR": "France",
		"ES": "Spain",
		"IT": "Italy",
		"IE": "Ireland",
		"NL": "Netherlands",
		"JP": "Japan",
		"CN": "China",
		"HK": "China",
		"SG": "Singapore",
		"AU": "Australia",
		"CH": "Switzerland",
		"SE": "Sweden",
		"DK": "Denmark",
		"NO": "Norway",
		"FI": "Finland",
		"BE": "Belgium",
		"AT": "Austria",
		"KR": "South Korea",
		"TW": "Taiwan",
		"IN": "India",
		"BR": "Brazil",
		"MX": "Mexico",
		"ZA": "South Africa",
		"SA": "Saudi Arabia",
		"MY": "Malaysia",
		"PL": "Poland",
		"ID": "Indonesia",
		"KW": "Kuwait",
		"QA": "Qatar",
		"North America": "North America",
		"Europe Developed": "Europe (Developed)",
		"Europe Emerging": "Europe (Emerging)",
		"Asia Developed": "Asia (Developed)",
		"Asia Emerging": "Asia (Emerging)",
		"Latin America": "Latin America",
		"Middle East": "Middle East",
		"Africa": "Africa",
		"Oceania": "Oceania",
	}
	ISIN_PREFIX_LENGTH = 2
	_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")

	@staticmethod
	def parse_order_date(date_str: str) -> datetime:
		"""Parse supported order date formats for chronological calculations."""
		for fmt in ComputeService._DATE_FORMATS:
			try:
				return datetime.strptime(date_str, fmt)
			except ValueError:
				continue
		return datetime.max

	@staticmethod
	def calculate_position(orders: list[dict[str, Any]], isin: str) -> dict[str, Any]:
		"""
		Calculate current position for a specific ISIN from order history.

		Args:
			orders: List of order dicts with date, isin, shares, amount_eur, status, price_per_share, order_type
			isin: ISIN code to calculate position for

		Returns:
			Dict with total_shares, average_cost, total_invested
		"""
		relevant_orders = sorted(
			[o for o in orders if o.get("isin") == isin and o.get("status", "").lower() == "finalizada"],
			key=lambda order: ComputeService.parse_order_date(str(order.get("date", ""))),
		)

		if not relevant_orders:
			return {"total_shares": 0.0, "average_cost": 0.0, "total_invested": 0.0}

		total_shares = Decimal("0")
		total_cost = Decimal("0")  # Cumulative cost basis
		average_cost = Decimal("0")  # Running average cost per share

		for order in relevant_orders:
			shares = Decimal(str(order.get("shares", 0)))
			order_type = order.get("order_type", "buy").lower()

			if order_type == "sell":
				# For sells: reduce shares and reduce cost by (shares sold * current average cost)
				# This maintains the cost basis correctly
				if total_shares > Decimal("0") and average_cost > Decimal("0"):
					cost_reduction = shares * average_cost
					total_shares -= shares
					total_cost -= cost_reduction
					# average_cost stays the same (cost basis per share doesn't change)
				else:
					# Edge case: selling without any prior buys (shouldn't happen, but handle gracefully)
					total_shares -= shares
					# Don't modify total_cost if we don't have a cost basis
			else:  # buy
				# Prioritize amount_eur as the actual cost basis if available
				amount_eur = order.get("amount_eur")
				if amount_eur is not None and amount_eur > 0:
					cost = Decimal(str(amount_eur))
				elif "price_per_share" in order and order["price_per_share"] is not None:
					price = Decimal(str(order["price_per_share"]))
					cost = shares * price
				else:
					cost = Decimal("0")

				total_shares += shares
				total_cost += cost
				# Recalculate average cost after each buy
				average_cost = total_cost / total_shares if total_shares > 0 else Decimal("0")

		return {
			"total_shares": float(total_shares),
			"average_cost": float(average_cost),
			"total_invested": float(total_cost),
		}

	@staticmethod
	def calculate_pnl(position: dict[str, Any], current_price: float) -> dict[str, Any]:
		"""
		Calculate profit/loss for a position.

		Args:
			position: Position dict with total_shares, average_cost, total_invested
			current_price: Current market price per share

		Returns:
			Dict with current_value, unrealized_pnl, unrealized_pnl_pct
		"""
		total_shares = position.get("total_shares", 0.0)
		total_invested = position.get("total_invested", 0.0)

		current_value = total_shares * current_price
		unrealized_pnl = current_value - total_invested
		unrealized_pnl_pct = (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0.0

		return {
			"current_value": current_value,
			"unrealized_pnl": unrealized_pnl,
			"unrealized_pnl_pct": unrealized_pnl_pct,
		}

	@staticmethod
	def calculate_portfolio_metrics(holdings: list[dict[str, Any]]) -> dict[str, Any]:
		"""
		Calculate overall portfolio metrics.

		Args:
			holdings: List of holdings with total_invested, current_value, unrealized_pnl

		Returns:
			Dict with total_invested, total_value, total_pnl, total_pnl_pct
		"""
		if not holdings:
			return {
				"total_invested": 0.0,
				"total_value": 0.0,
				"total_pnl": 0.0,
				"total_pnl_pct": 0.0,
			}

		total_invested = sum(h.get("total_invested", 0.0) for h in holdings)
		total_value = sum(h.get("current_value", 0.0) for h in holdings)
		total_pnl = total_value - total_invested
		total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

		return {
			"total_invested": total_invested,
			"total_value": total_value,
			"total_pnl": total_pnl,
			"total_pnl_pct": total_pnl_pct,
		}

	@staticmethod
	def calculate_allocation_by_key(holdings: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
		"""
		Calculate allocation breakdown by a specific key (e.g., geography, sector, asset_type).

		Args:
			holdings: List of holdings with current_value and the specified key
			key: Key to group by (e.g., 'geography', 'sector', 'asset_type')

		Returns:
			List of dicts with category, value, percentage
		"""
		if not holdings:
			return []

		total_value = sum(h.get("current_value", 0.0) for h in holdings)
		if total_value == 0:
			return []

		# Group by key
		groups: dict[str, float] = {}
		for h in holdings:
			category = h.get(key, "Unknown")
			value = h.get("current_value", 0.0)
			groups[category] = groups.get(category, 0.0) + value

		# Calculate percentages
		result = []
		for category, value in sorted(groups.items(), key=lambda x: x[1], reverse=True):
			result.append(
				{
					"category": category,
					"value": value,
					"percentage": (value / total_value * 100) if total_value > 0 else 0.0,
				}
			)

		return result

	@staticmethod
	def calculate_time_series(orders: list[dict[str, Any]], prices: dict[str, float]) -> list[dict[str, Any]]:
		"""
		Calculate invested vs current value over time.

		Args:
			orders: List of orders sorted by date
			prices: Dict mapping ISIN to current price

		Returns:
			List of dicts with date, invested_value, current_value
		"""
		if not orders:
			return []

		# Sort orders chronologically before applying buys/sells.
		sorted_orders = sorted(orders, key=lambda x: ComputeService.parse_order_date(str(x.get("date", ""))))

		time_series = []
		cumulative_invested = Decimal("0")
		positions: dict[Any, Any] = {}  # ISIN -> shares (Decimal)
		average_costs: dict[Any, Any] = {}  # ISIN -> average cost per share (Decimal)

		for order in sorted_orders:
			if order.get("status", "").lower() != "finalizada":
				continue

			date = order.get("date")
			isin = order.get("isin")
			if not isin:
				continue
			isin = str(isin)  # narrow type to str
			shares = Decimal(str(order.get("shares", 0)))
			order_type = str(order.get("order_type", "buy")).lower()

			if order_type == "sell":
				# For sells: reduce shares and cost by (shares sold * average cost)
				if isin in positions and positions[isin] > Decimal("0") and isin in average_costs:
					cost_reduction = shares * average_costs[isin]
					cumulative_invested -= cost_reduction
					positions[isin] = positions.get(isin, Decimal("0")) - shares
				else:
					# Edge case: selling without prior buys
					positions[isin] = positions.get(isin, Decimal("0")) - shares
			else:  # buy
				# Calculate actual cost using price_per_share if available
				if "price_per_share" in order and order["price_per_share"] is not None:
					price_per_share = Decimal(str(order["price_per_share"]))
					cost = shares * price_per_share
				else:
					# Fallback to amount_eur
					cost = Decimal(str(order.get("amount_eur", 0)))

				cumulative_invested += cost
				old_shares = positions.get(isin, Decimal("0"))
				new_shares = old_shares + shares

				# Update average cost for this ISIN
				if isin in average_costs and old_shares > Decimal("0"):
					old_cost = old_shares * average_costs[isin]
					new_cost = old_cost + cost
					average_costs[isin] = new_cost / new_shares
				else:
					average_costs[isin] = cost / shares if shares > Decimal("0") else Decimal("0")

				positions[isin] = new_shares

			# Calculate current value with current prices
			current_value = 0.0
			for pos_isin, pos_shares in positions.items():
				price = prices.get(pos_isin, 0.0)
				current_value += float(pos_shares) * price

			time_series.append(
				{
					"date": date,
					"invested_value": float(cumulative_invested),
					"current_value": current_value,
				}
			)

		return time_series

	@staticmethod
	def is_price_stale(last_update: str, threshold_days: int = 3) -> bool:
		"""
		Check if a price is stale (older than threshold).

		Args:
			last_update: ISO format datetime string
			threshold_days: Number of days to consider stale (default: 3)

		Returns:
			True if price is stale, False otherwise
		"""
		if not last_update:
			return True

		try:
			last_update_dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
			now = datetime.now(last_update_dt.tzinfo)
			age_days = (now - last_update_dt).days
			return age_days > threshold_days
		except (ValueError, AttributeError):
			return True

	@staticmethod
	def calculate_diversification_score(allocations: list[dict[str, Any]]) -> float:
		"""
		Calculate diversification score using Herfindahl-Hirschman Index (HHI).

		Args:
			allocations: List of dicts with 'percentage' key

		Returns:
			Score from 0-100, where 100 is perfectly diversified
		"""
		if not allocations:
			return 0.0

		# Calculate HHI (sum of squared percentages)
		hhi = sum((a.get("percentage", 0) / 100) ** 2 for a in allocations)

		# Normalize to 0-100 scale (lower HHI = better diversification)
		# HHI ranges from 1/n (perfect diversification) to 1 (concentrated)
		# Convert to score where 100 is best
		n = len(allocations)
		min_hhi = 1.0 / n if n > 0 else 1.0
		max_hhi = 1.0

		if max_hhi == min_hhi:
			return 100.0

		normalized = (max_hhi - hhi) / (max_hhi - min_hhi)
		return normalized * 100

	@staticmethod
	def calculate_weighted_average(items: list[dict[str, Any]], value_key: str, weight_key: str) -> float:
		"""
		Calculate weighted average.

		Args:
			items: List of items
			value_key: Key for the value to average
			weight_key: Key for the weight

		Returns:
			Weighted average
		"""
		total_weight = sum(item.get(weight_key, 0.0) for item in items)
		if total_weight == 0:
			return 0.0

		weighted_sum = sum(item.get(value_key, 0.0) * item.get(weight_key, 0.0) for item in items)
		return weighted_sum / total_weight

	@staticmethod
	def normalize_geo_keys(geo: dict[str, float]) -> dict[str, float]:
		"""Normalize geography keys to ISO country codes where possible."""
		if not geo:
			return {}

		# mapping of common full names to codes
		name_to_iso = {
			"United States": "US",
			"USA": "US",
			"Canada": "CA",
			"Germany": "DE",
			"France": "FR",
			"Spain": "ES",
			"Italy": "IT",
			"Ireland": "IE",
			"Netherlands": "NL",
			"United Kingdom": "GB",
			"UK": "GB",
			"United States of America": "US",
			"U.S.": "US",
			"U.S.A.": "US",
			"Japan": "JP",
			"China": "CN",
			"Hong Kong": "CN",
			"Singapore": "SG",
			"Australia": "AU",
			"Switzerland": "CH",
			"Sweden": "SE",
			"Denmark": "DK",
			"Norway": "NO",
			"Finland": "FI",
			"Belgium": "BE",
			"Austria": "AT",
			"South Korea": "KR",
			"Taiwan": "TW",
			"India": "IN",
			"Brazil": "BR",
			"Mexico": "MX",
			"South Africa": "ZA",
			"Saudi Arabia": "SA",
			"United Arab Emirates": "AE",
			"Malaysia": "MY",
			"Poland": "PL",
			"Indonesia": "ID",
			"Kuwait": "KW",
			"Qatar": "QA",
			ComputeService.OTHER_ALLOCATION_LABEL: ComputeService.OTHER_ALLOCATION_LABEL,
			"Other": ComputeService.OTHER_ALLOCATION_LABEL,
			"Others": ComputeService.OTHER_ALLOCATION_LABEL,
		}
		normalized: dict[str, float] = {}
		for k, v in geo.items():
			code = name_to_iso.get(k, k)
			if code == "HK":
				code = "CN"
			# Only keep simple tokens (avoid long region descriptions)
			normalized[code] = normalized.get(code, 0.0) + float(v)
		return normalized

	@staticmethod
	def get_fallback_geo_alloc(isin: str) -> dict[str, float]:
		"""Infer country from ISIN prefix if no metadata available."""
		# fallback country inference from ISIN prefix
		isin_str = str(isin)
		country_code = isin_str[: ComputeService.ISIN_PREFIX_LENGTH] if len(isin_str) >= ComputeService.ISIN_PREFIX_LENGTH else "XX"
		fallback_geo_map = {
			"IE": "IE",
			"DE": "DE",
			"FR": "FR",
			"NL": "NL",
			"ES": "ES",
			"IT": "IT",
			"GB": "GB",
			"US": "US",
			"CA": "CA",
			"JP": "JP",
			"CN": "CN",
			"HK": "CN",
			"SG": "SG",
			"AU": "AU",
		}
		return {fallback_geo_map.get(country_code, "Other"): 1.0}

	@staticmethod
	def build_enriched_holdings(
		unique_isins: set[str], finalized_orders: list[dict[str, Any]], prices: dict[str, Any], instrument_map: dict[str, Any]
	) -> list[dict[str, Any]]:
		"""Build positions with enriched metadata (asset type, sector, geography)."""
		holdings: list[dict[str, Any]] = []
		for isin in unique_isins:
			position = ComputeService.calculate_position(finalized_orders, isin)
			if position["total_shares"] <= 0:
				continue

			price_data = prices.get(isin, {})
			latest_price = price_data.get("price") or position["average_cost"]
			name = price_data.get("name") or isin
			pnl_data = ComputeService.calculate_pnl(position, latest_price)

			meta = instrument_map.get(isin, {})
			asset_type = meta.get("type") or price_data.get("asset_type") or "Fund"
			sector_alloc = meta.get("sector_allocation") or price_data.get("sector_allocation") or {"Diversified": 1.0}
			geo_alloc_raw = meta.get("country_allocation") or price_data.get("country_allocation") or {}
			geo_alloc = ComputeService.normalize_geo_keys(geo_alloc_raw)

			if not geo_alloc:
				geo_alloc = ComputeService.get_fallback_geo_alloc(isin)

			holdings.append(
				{
					"isin": isin,
					"name": name,
					"current_value": pnl_data["current_value"],
					"asset_type": asset_type,
					"sector_allocation": sector_alloc,
					"geo_allocation": geo_alloc,
				}
			)
		return holdings

	@staticmethod
	def calculate_allocations(holdings: list[dict[str, Any]], total_value: float) -> dict[str, Any]:
		"""Helper to calculate allocations by instrument, geography, sector, and asset type."""
		by_instrument: dict[str, float] = {}
		by_geography: dict[str, float] = {}
		by_sector: dict[str, float] = {}
		by_asset_type: dict[str, float] = {}
		crypto_value = 0.0

		if total_value <= 0:
			return {
				"by_instrument": {},
				"by_geography": {},
				"by_sector": {},
				"by_asset_type": {},
				"crypto_value": 0.0,
			}

		for h in holdings:
			name = str(h["name"])
			value = float(h.get("current_value", 0.0))
			asset_type = str(h.get("asset_type", "Unknown"))

			# By instrument/fund excludes crypto. Crypto remains visible in asset-type allocation.
			if asset_type != "Crypto":
				by_instrument[name] = float(value)

			# By asset type
			prev_asset = by_asset_type.get(asset_type, 0.0)
			by_asset_type[asset_type] = float(prev_asset) + value
			if asset_type == "Crypto":
				crypto_value = float(crypto_value) + value

			# Weighted geography/sector (exclude crypto)
			if asset_type != "Crypto":
				geo_alloc = h.get("geo_allocation", {})
				for geo, weight in geo_alloc.items():
					by_geography[str(geo)] = by_geography.get(str(geo), 0.0) + (float(value) * float(weight))

				sector_alloc = h.get("sector_allocation", {})
				for sector, weight in sector_alloc.items():
					by_sector[str(sector)] = by_sector.get(str(sector), 0.0) + (float(value) * float(weight))

		# Transform and sort
		by_instrument = dict(sorted(by_instrument.items(), key=lambda x: x[1], reverse=True))

		by_geography_named: dict[str, float] = {}
		for code, value in by_geography.items():
			label = ComputeService.COUNTRY_NAMES.get(code, code)
			by_geography_named[label] = by_geography_named.get(label, 0.0) + value
		by_geography_named = dict(sorted(by_geography_named.items(), key=lambda x: x[1], reverse=True))
		by_sector = dict(sorted(by_sector.items(), key=lambda x: x[1], reverse=True))
		by_asset_type = dict(sorted(by_asset_type.items(), key=lambda x: x[1], reverse=True))

		return {
			"by_instrument": by_instrument,
			"by_geography": by_geography_named,
			"by_sector": by_sector,
			"by_asset_type": by_asset_type,
			"crypto_value": crypto_value,
		}
