"""Router for order management (CSV import, CRUD operations)."""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.config import settings
from app.models.order import OrderCreate, OrderResponse, OrderUpdate
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.websocket import manager as websocket_manager
from app.services.historical_price_service import HistoricalPriceService
from app.services.storage_service import StorageService
from app.utils.csv_parser import CryptoExchangeCSVParser, SpanishOrderCSVParser
from app.utils.validators import is_crypto_symbol

router = APIRouter(prefix="/api/orders", tags=["orders"])
logger = logging.getLogger(__name__)


def get_websocket_manager():
	"""Return global websocket manager instance."""
	return websocket_manager


def _filter_orders(
	orders: list[dict[str, Any]],
	isin: str | None,
	ticker: str | None,
	order_type: str | None,
	status: str | None,
	date_from: str | None,
	date_to: str | None,
) -> list[dict[str, Any]]:
	"""Apply filter parameters to an orders list."""
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


def _parse_date_for_sorting(date_str: str) -> str:
	"""
	Convert date to sortable format (YYYY-MM-DD).

	Handles both DD/MM/YYYY and YYYY-MM-DD formats.
	"""
	ISO_LEN = 10
	DATE_PARTS = 3
	if not date_str:
		return ""

	# Check if already in YYYY-MM-DD format
	if len(date_str) == ISO_LEN and date_str[4] == "-":
		return date_str

	# Convert DD/MM/YYYY to YYYY-MM-DD
	if "/" in date_str:
		parts = date_str.split("/")
		if len(parts) == DATE_PARTS:
			return f"{parts[2]}-{parts[1]}-{parts[0]}"

	return date_str


def _sort_orders(orders: list[dict[str, Any]], sort_by: str, sort_order: str) -> None:
	"""In-place sort of orders by given field and order."""
	if sort_by in {"date", "amount_eur", "shares"}:
		reverse = sort_order.lower() == "desc"
		if sort_by == "date":
			# Special handling for dates to support both DD/MM/YYYY and YYYY-MM-DD
			orders.sort(key=lambda x: _parse_date_for_sorting(x.get("date", "")), reverse=reverse)
		else:
			orders.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)


def _paginate_orders(orders: list[dict[str, Any]], offset: int, limit: int | None) -> list[dict[str, Any]]:
	"""Return paginated slice of orders."""
	slice_ = orders[offset:]
	if limit:
		slice_ = slice_[:limit]
	return slice_


@router.post("/import-csv")
async def import_csv(
	file: UploadFile = File(...),
	current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
	"""
	Import orders from a Spanish bank CSV file.

	Expected CSV format:
	- Headers: Fecha de la orden, ISIN, Importe estimado, Nº de participaciones, Estado
	- Date format: DD/MM/YYYY
	- Decimal format: Spanish (1.234,56)
	- Status: Finalizada (accepted), Rechazada (rejected)

	Returns:
		Dict with imported_count, rejected_count, errors list
	"""
	logger.info(f"CSV import started - User: {current_user.username}, File: {file.filename}")

	# Validate file type
	if not file.filename.endswith(".csv"):
		logger.warning(f"Invalid file type attempted: {file.filename}")
		raise HTTPException(status_code=400, detail="File must be a CSV")

	# Read file content
	try:
		content = await file.read()
		content_str = content.decode("utf-8")
		logger.debug(f"CSV file read successfully - Size: {len(content_str)} bytes")
	except Exception as e:
		logger.error(f"Error reading CSV file: {e!s}")
		raise HTTPException(status_code=400, detail=f"Error reading file: {e!s}") from e

	try:
		orders, errors = _detect_and_parse_csv(content_str)
		logger.info(f"CSV parsed - Orders: {len(orders)}, Errors: {len(errors)}")

		if not orders and errors:
			return {
				"success": False,
				"imported_count": 0,
				"rejected_count": 0,
				"errors": errors,
				"message": "No orders were imported due to errors",
			}

		users_file = settings.DATA_DIR / "users.json"
		new_count, updated_count = StorageService.update_user_data(
			current_user.username, lambda data: _merge_orders(data, orders), users_file
		)

		logger.info(f"CSV import completed successfully - User: {current_user.username}, New: {new_count}, Updated: {updated_count}")

		# Broadcast update via WebSocket
		manager = get_websocket_manager()
		await manager.broadcast_to_user(
			current_user.username,
			{
				"type": "orders_imported",
				"count": len(orders),
				"timestamp": datetime.now(UTC).isoformat(),
			},
		)

		return {
			"success": True,
			"imported_count": new_count,
			"updated_count": updated_count,
			"rejected_count": len([o for o in orders if o.get("status") == "rechazada"]),
			"errors": errors,
			"message": f"Successfully imported {new_count} new orders and updated {updated_count} existing orders",
		}

	except Exception as e:
		logger.error(f"Unexpected error in import_csv: {e}")
		raise HTTPException(status_code=500, detail=f"Error processing CSV: {e!s}") from e


def _detect_and_parse_csv(content_str: str) -> tuple[list[dict[str, Any]], list[str]]:
	"""Detect CSV type and parse accordingly."""
	content_str = content_str.lstrip("\ufeff")
	first_line = content_str.splitlines()[0] if content_str else ""

	# Crypto CSV detection
	is_crypto_csv = "Date(UTC" in first_line and "Spend Amount" in first_line

	if is_crypto_csv:
		logger.info("Detected crypto exchange CSV format")
		parser = CryptoExchangeCSVParser()
		return parser.parse_csv(content_str)
	else:
		logger.info("Detected Spanish bank CSV format")
		parser = SpanishOrderCSVParser()
		return parser.parse_csv(content_str)


def _merge_orders(user_data: dict[str, Any], new_orders: list[dict[str, Any]]) -> tuple[int, int]:
	"""Merge new orders into user data, updating duplicates."""
	if "orders" not in user_data:
		user_data["orders"] = []

	existing_orders = user_data["orders"]
	new_count = 0
	updated_count = 0

	for order in new_orders:
		# Detect duplicates: orders with same ISIN, date, and shares
		order_key = (order.get("isin"), order.get("date"), order.get("shares"))

		existing_idx = None
		for idx, existing in enumerate(existing_orders):
			existing_key = (existing.get("isin"), existing.get("date"), existing.get("shares"))
			if order_key == existing_key:
				existing_idx = idx
				break

		if existing_idx is not None:
			existing_orders[existing_idx] = order
			updated_count += 1
		else:
			existing_orders.append(order)
			new_count += 1

	# Sort by date (most recent first)
	user_data["orders"].sort(key=lambda x: x.get("date", ""), reverse=True)
	return new_count, updated_count


@router.get("/")
async def get_orders(
	current_user: User = Depends(get_current_user),
	isin: str | None = Query(None, description="Filter by ISIN"),
	ticker: str | None = Query(None, description="Filter by ticker symbol"),
	order_type: str | None = Query(None, description="Filter by order type (buy/sell)"),
	status: str | None = Query(None, description="Filter by status (Finalizada/Rechazada)"),
	date_from: str | None = Query(None, description="Filter orders from this date (YYYY-MM-DD)"),
	date_to: str | None = Query(None, description="Filter orders up to this date (YYYY-MM-DD)"),
	sort_by: str = Query("date", description="Sort by field: date, amount_eur, shares"),
	sort_order: str = Query("desc", description="Sort order: asc or desc"),
	limit: int | None = Query(None, ge=1, le=1000, description="Limit number of results"),
	offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> dict[str, Any]:
	"""
	Get orders for current user with filtering, sorting, and pagination.

	Query Parameters:
		- isin: Filter by ISIN code
		- ticker: Filter by ticker symbol
		- order_type: Filter by buy/sell
		- status: Filter by order status
		- date_from: Start date (inclusive)
		- date_to: End date (inclusive)
		- sort_by: Field to sort by (date, amount_eur, shares)
		- sort_order: asc or desc
		- limit: Maximum number of results
		- offset: Skip this many results (for pagination)

	Returns:
		Dict with orders list, total count, and filter info
	"""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	user_data = users[current_user.username]
	orders = user_data.get("orders", [])

	# Filter
	filtered_orders = _filter_orders(orders, isin, ticker, order_type, status, date_from, date_to)
	# Sort
	_sort_orders(filtered_orders, sort_by, sort_order)
	total_count = len(filtered_orders)
	# Paginate
	paginated_orders = _paginate_orders(filtered_orders, offset, limit)

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


@router.get("/{order_id}")
async def get_order(order_id: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get specific order by ID."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	orders = users[current_user.username].get("orders", [])

	# Find order by ID
	order = next((o for o in orders if o.get("id") == order_id), None)

	if not order:
		raise HTTPException(status_code=404, detail="Order not found")

	return order


@router.post("/", status_code=201)
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user)) -> OrderResponse:
	"""
	Create a new order manually.

	This allows users to add individual buy/sell orders without CSV import.
	Automatically fetches the historical price for the order date.
	"""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	# Generate unique order ID
	order_id = str(uuid.uuid4())

	# Fetch historical price if not provided
	price_per_share = order_data.price_per_share
	price_currency = order_data.price_currency
	price_date = order_data.price_date

	if price_per_share is None:
		logger.info(f"Fetching historical price for {order_data.isin} on {order_data.date}")
		price_data = await HistoricalPriceService.get_price_on_date(order_data.isin, order_data.date)

		if price_data:
			price_per_share = price_data["price"]
			price_currency = price_data["currency"]
			price_date = price_data["date"]
			logger.info(f"Retrieved historical price: {price_per_share} {price_currency} on {price_date}")
		else:
			# Fallback to calculated price
			price_per_share = order_data.amount_eur / order_data.shares
			price_currency = "EUR"
			price_date = order_data.date
			logger.warning(f"Could not fetch historical price, using calculated: {price_per_share:.4f} EUR")

	# Create order with ID and timestamp
	derived_asset_type = "Crypto" if is_crypto_symbol(order_data.isin) else None

	new_order = {
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

	# Add to user's orders
	if "orders" not in users[current_user.username]:
		users[current_user.username]["orders"] = []

	users[current_user.username]["orders"].append(new_order)

	# Sort by date (most recent first)
	users[current_user.username]["orders"].sort(key=lambda x: x.get("date", ""), reverse=True)

	# Save
	StorageService.save_json(users_file, users)

	# Broadcast update via WebSocket
	manager = get_websocket_manager()
	await manager.broadcast_to_user(
		current_user.username,
		{
			"type": "order_created",
			"order_id": order_id,
			"timestamp": datetime.now(UTC).isoformat(),
		},
	)

	return OrderResponse(**new_order)


@router.put("/{order_id}")
async def update_order(
	order_id: str,
	order_data: OrderUpdate,
	current_user: User = Depends(get_current_user),
) -> OrderResponse:
	"""Update an existing order."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	orders = users[current_user.username].get("orders", [])

	# Find order index
	order_idx = next((i for i, o in enumerate(orders) if o.get("id") == order_id), None)

	if order_idx is None:
		raise HTTPException(status_code=404, detail="Order not found")

	# Update order fields
	order = orders[order_idx]
	update_dict = order_data.model_dump(exclude_unset=True)

	for key, value in update_dict.items():
		if value is not None:
			order[key] = value

	# Auto-derive asset_type if missing and isin suggests crypto
	if not order.get("asset_type") and is_crypto_symbol(order.get("isin", "")):
		order["asset_type"] = "Crypto"

	# Re-sort if date changed
	if "date" in update_dict:
		users[current_user.username]["orders"].sort(key=lambda x: x.get("date", ""), reverse=True)

	# Save
	StorageService.save_json(users_file, users)

	# Broadcast update via WebSocket
	manager = get_websocket_manager()
	await manager.broadcast_to_user(
		current_user.username,
		{
			"type": "order_updated",
			"order_id": order_id,
			"timestamp": datetime.now(UTC).isoformat(),
		},
	)

	return OrderResponse(**order)


@router.delete("/all", status_code=204)
async def delete_all_orders(current_user: User = Depends(get_current_user)):
	"""Delete all orders for the current user."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	# Clear all orders
	users[current_user.username]["orders"] = []

	# Save
	StorageService.save_json(users_file, users)

	# Broadcast update via WebSocket
	manager = get_websocket_manager()
	await manager.broadcast_to_user(
		current_user.username,
		{
			"type": "orders_cleared",
			"timestamp": datetime.now(UTC).isoformat(),
		},
	)


@router.delete("/{order_id}", status_code=204)
async def delete_order(order_id: str, current_user: User = Depends(get_current_user)):
	"""Delete an order."""
	users_file = settings.DATA_DIR / "users.json"
	users = StorageService.load_json(users_file, default={})

	if current_user.username not in users:
		raise HTTPException(status_code=404, detail="User not found")

	orders = users[current_user.username].get("orders", [])

	# Find and remove order
	order_idx = next((i for i, o in enumerate(orders) if o.get("id") == order_id), None)

	if order_idx is None:
		raise HTTPException(status_code=404, detail="Order not found")

	orders.pop(order_idx)

	# Save
	StorageService.save_json(users_file, users)

	# Broadcast update via WebSocket
	manager = get_websocket_manager()
	await manager.broadcast_to_user(
		current_user.username,
		{
			"type": "order_deleted",
			"order_id": order_id,
			"timestamp": datetime.now(UTC).isoformat(),
		},
	)
