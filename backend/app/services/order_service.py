import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from app.config import settings
from app.models.order import OrderCreate
from app.services.storage_service import StorageService
from app.utils.csv_parser import CryptoExchangeCSVParser, SpanishOrderCSVParser
from app.utils.validators import is_crypto_symbol


class OrderService:
	"""Service for order filtering, import, and persistence operations."""

	@staticmethod
	def _normalized_decimal(value: Any, places: str) -> str:
		"""Return a stable decimal string for order fingerprinting."""
		try:
			decimal_value = Decimal(str(value))
		except (InvalidOperation, TypeError, ValueError):
			decimal_value = Decimal("0")
		return str(decimal_value.quantize(Decimal(places), rounding=ROUND_HALF_UP))

	@staticmethod
	def order_fingerprint(order: dict[str, Any]) -> tuple[str, str, str, str, str]:
		"""Return the duplicate-detection fingerprint for an order."""
		return (
			str(order.get("date", "")).strip(),
			str(order.get("isin", "")).strip().upper(),
			str(order.get("order_type", "buy")).strip().lower(),
			OrderService._normalized_decimal(order.get("amount_eur", 0), "0.01"),
			OrderService._normalized_decimal(order.get("shares", 0), "0.0000000001"),
		)

	@staticmethod
	def classify_import_orders(existing_orders: list[dict[str, Any]], parsed_orders: list[dict[str, Any]]) -> dict[str, Any]:
		"""Classify parsed orders as new or already present."""
		existing_by_fingerprint = {OrderService.order_fingerprint(order): order for order in existing_orders}
		seen_fingerprints = set(existing_by_fingerprint)
		classified_orders: list[dict[str, Any]] = []
		new_count = 0
		skipped_count = 0

		for order in parsed_orders:
			fingerprint = OrderService.order_fingerprint(order)
			existing_order = existing_by_fingerprint.get(fingerprint)
			classified = dict(order)
			if fingerprint in seen_fingerprints:
				classified["import_status"] = "already_present"
				classified["existing_order_id"] = existing_order.get("id") if existing_order else None
				skipped_count += 1
			else:
				classified["import_status"] = "new"
				classified["existing_order_id"] = None
				seen_fingerprints.add(fingerprint)
				new_count += 1
			classified_orders.append(classified)

		return {"orders": classified_orders, "new_count": new_count, "skipped_count": skipped_count}

	@staticmethod
	def filter_orders(
		orders: list[dict[str, Any]],
		isin: str | None,
		ticker: str | None,
		order_type: str | None,
		status: str | None,
		date_from: str | None,
		date_to: str | None,
	) -> list[dict[str, Any]]:
		"""Return orders matching the provided optional filters."""
		filtered = orders
		if isin:
			filtered = [o for o in filtered if o.get("isin", "").upper() == isin.upper()]
		if ticker:
			filtered = [o for o in filtered if o.get("ticker", "").upper() == ticker.upper()]
		if order_type:
			filtered = [o for o in filtered if o.get("order_type", "") == order_type.lower()]
		if status:
			filtered = [o for o in filtered if o.get("status", "").lower() == status.lower()]
		if date_from:
			filtered = [o for o in filtered if o.get("date", "") >= date_from]
		if date_to:
			filtered = [o for o in filtered if o.get("date", "") <= date_to]
		return filtered

	@staticmethod
	def parse_date_for_sorting(date_str: str) -> str:
		"""Normalize supported date strings for lexical sorting."""
		ISO_LEN = 10
		DATE_PARTS = 3
		if not date_str:
			return ""
		if len(date_str) == ISO_LEN and date_str[4] == "-":
			return date_str
		if "/" in date_str:
			parts = date_str.split("/")
			if len(parts) == DATE_PARTS:
				return f"{parts[2]}-{parts[1]}-{parts[0]}"
		return date_str

	@staticmethod
	def sort_orders(orders: list[dict[str, Any]], sort_by: str, sort_order: str) -> None:
		"""Sort orders in-place by a supported field."""
		if sort_by in {"date", "amount_eur", "shares"}:
			reverse = sort_order.lower() == "desc"
			if sort_by == "date":
				orders.sort(key=lambda x: OrderService.parse_date_for_sorting(x.get("date", "")), reverse=reverse)
			else:
				orders.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

	@staticmethod
	def paginate_orders(orders: list[dict[str, Any]], offset: int, limit: int | None) -> list[dict[str, Any]]:
		"""Return a page of orders from offset with optional limit."""
		if not orders:
			return []

		slice_ = orders[offset:]
		if limit:
			slice_ = slice_[:limit]
		return slice_

	@staticmethod
	def detect_and_parse_csv(content_str: str) -> tuple[list[dict[str, Any]], list[str]]:
		"""Parse an uploaded CSV using the matching order parser."""
		content_str = content_str.lstrip("\ufeff")
		first_line = content_str.splitlines()[0] if content_str else ""
		is_crypto_csv = "Date(UTC" in first_line and "Spend Amount" in first_line

		if is_crypto_csv:
			parser = CryptoExchangeCSVParser()
			return parser.parse_csv(content_str)
		else:
			parser = SpanishOrderCSVParser()
			return parser.parse_csv(content_str)

	@staticmethod
	def merge_orders(user_data: dict[str, Any], new_orders: list[dict[str, Any]]) -> tuple[int, int]:
		"""Merge parsed orders into user data and return new/skipped counts."""
		if "orders" not in user_data:
			user_data["orders"] = []

		existing_orders = user_data["orders"]
		new_count: int = 0
		skipped_count: int = 0
		existing_fingerprints = {OrderService.order_fingerprint(order) for order in existing_orders}

		for order in new_orders:
			fingerprint = OrderService.order_fingerprint(order)
			if fingerprint in existing_fingerprints:
				skipped_count += 1
				continue
			existing_orders.append(order)
			existing_fingerprints.add(fingerprint)
			new_count += 1

		user_data["orders"].sort(key=lambda x: str(x.get("date", "")), reverse=True)
		return new_count, skipped_count

	@staticmethod
	def import_orders_atomic(username: str, orders: list[dict[str, Any]]) -> tuple[int, int]:
		"""Import parsed orders into a user's order list atomically."""
		users_file = settings.DATA_DIR / "users.json"
		counts = {"new": 0, "skipped": 0}

		def update_fn(users: dict[str, Any]) -> dict[str, Any]:
			user_data = users.setdefault(username, {})
			new_count, skipped_count = OrderService.merge_orders(user_data, orders)
			counts["new"] = new_count
			counts["skipped"] = skipped_count
			return users

		StorageService.update_json(users_file, update_fn, default={})
		return counts["new"], counts["skipped"]

	@staticmethod
	def build_manual_order(order_data: OrderCreate) -> dict[str, Any]:
		"""Build a manual order payload without mutating stored user data."""
		order_id = str(uuid.uuid4())
		price_per_share = order_data.price_per_share
		price_currency = order_data.price_currency
		price_date = order_data.price_date

		if price_per_share is None:
			price_per_share = order_data.amount_eur / order_data.shares
			price_currency = "EUR"
			price_date = order_data.date

		derived_asset_type = "Crypto" if is_crypto_symbol(order_data.isin) else None

		return {
			"id": order_id,
			"date": order_data.date,
			"isin": order_data.isin,
			"ticker": order_data.ticker,
			"amount_eur": order_data.amount_eur,
			"shares": order_data.shares,
			"price_per_share": price_per_share,
			"price_currency": price_currency,
			"price_date": price_date,
			"order_type": order_data.order_type,
			"status": order_data.status,
			"asset_type": derived_asset_type,
			"notes": order_data.notes,
			"created_at": datetime.now(UTC).isoformat(),
		}

	@staticmethod
	def get_user_orders(username: str, **filters: Any) -> dict[str, Any]:
		"""Get orders for a user with filtering and pagination."""
		users_file = settings.DATA_DIR / "users.json"
		users = StorageService.load_json(users_file, default={})

		if username not in users:
			return {"orders": [], "total": 0}

		orders = users[username].get("orders", [])

		# Extract filters
		isin = filters.get("isin")
		ticker = filters.get("ticker")
		order_type = filters.get("order_type")
		status = filters.get("status")
		date_from = filters.get("date_from")
		date_to = filters.get("date_to")
		sort_by = filters.get("sort_by", "date")
		sort_order = filters.get("sort_order", "desc")
		limit = filters.get("limit")
		offset = filters.get("offset", 0)

		filtered_orders = OrderService.filter_orders(orders, isin, ticker, order_type, status, date_from, date_to)
		OrderService.sort_orders(filtered_orders, sort_by, sort_order)
		total_count = len(filtered_orders)
		paginated_orders = OrderService.paginate_orders(filtered_orders, offset, limit)

		return {
			"orders": paginated_orders,
			"total": total_count,
			"offset": offset,
			"limit": limit,
			"filters": {
				"isin": isin,
				"ticker": ticker,
				"order_type": order_type,
				"status": status,
				"date_from": date_from,
				"date_to": date_to,
			},
			"sort": {"by": sort_by, "order": sort_order},
		}

	@staticmethod
	def get_order_by_id(username: str, order_id: str) -> dict[str, Any] | None:
		"""Get a specific order for a user."""
		users_file = settings.DATA_DIR / "users.json"
		users = StorageService.load_json(users_file, default={})

		if username not in users:
			return None

		orders = users[username].get("orders", [])
		return next((o for o in orders if o.get("id") == order_id), None)

	@staticmethod
	def create_manual_order_atomic(username: str, order_data: OrderCreate) -> dict[str, Any]:
		"""Create an order and save it atomically."""
		users_file = settings.DATA_DIR / "users.json"
		new_order = OrderService.build_manual_order(order_data)

		def update_fn(users: dict[str, Any]) -> dict[str, Any]:
			if username not in users:
				users[username] = {}
			users[username].setdefault("orders", [])
			users[username]["orders"].append(new_order)
			users[username]["orders"].sort(key=lambda x: str(x.get("date", "")), reverse=True)
			return users

		StorageService.update_json(users_file, update_fn, default={})
		return new_order

	@staticmethod
	def update_order_atomic(username: str, order_id: str, order_update_data: dict[str, Any]) -> dict[str, Any] | None:
		"""Update an order atomically."""
		users_file = settings.DATA_DIR / "users.json"

		def update_fn(users: dict[str, Any]) -> dict[str, Any]:
			if username not in users:
				return users

			orders = users[username].get("orders", [])
			idx = next((i for i, o in enumerate(orders) if o.get("id") == order_id), None)

			if idx is None:
				return users

			order = orders[idx]
			for key, value in order_update_data.items():
				if value is not None:
					order[key] = value

			if not order.get("asset_type") and is_crypto_symbol(order.get("isin", "")):
				order["asset_type"] = "Crypto"

			if "date" in order_update_data:
				orders.sort(key=lambda x: str(x.get("date", "")), reverse=True)

			return users

		updated_users = StorageService.update_json(users_file, update_fn, default={})
		orders = updated_users.get(username, {}).get("orders", [])
		return next((o for o in orders if o.get("id") == order_id), None)

	@staticmethod
	def delete_order_atomic(username: str, order_id: str) -> bool:
		"""Delete an order atomically."""
		users_file = settings.DATA_DIR / "users.json"
		deleted = False

		def update_fn(users: dict[str, Any]) -> dict[str, Any]:
			nonlocal deleted
			if username not in users:
				return users
			orders = users[username].get("orders", [])
			initial_len = len(orders)
			users[username]["orders"] = [o for o in orders if o.get("id") != order_id]
			if len(users[username]["orders"]) < initial_len:
				deleted = True
			return users

		StorageService.update_json(users_file, update_fn, default={})
		return deleted

	@staticmethod
	def clear_all_orders_atomic(username: str) -> None:
		"""Clear all orders for a user atomically."""
		users_file = settings.DATA_DIR / "users.json"

		def update_fn(users: dict[str, Any]) -> dict[str, Any]:
			if username in users:
				users[username]["orders"] = []
			return users

		StorageService.update_json(users_file, update_fn, default={})
