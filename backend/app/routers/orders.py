"""Router for order management (CSV import, CRUD operations)."""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.models.order import OrderCreate, OrderResponse, OrderUpdate
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.websocket import manager as websocket_manager
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/orders", tags=["orders"])
logger = logging.getLogger(__name__)


def get_websocket_manager():
	"""Return global websocket manager instance."""
	return websocket_manager


@router.post("/import-csv")
async def import_csv(
	file: UploadFile = File(...),
	current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
	"""Import orders from a bank CSV file."""
	logger.info(f"CSV import started - User: {current_user.username}, File: {file.filename}")

	if not file.filename.endswith(".csv"):
		raise HTTPException(status_code=400, detail="File must be a CSV")

	try:
		content = await file.read()
		content_str = content.decode("utf-8")
	except Exception as e:
		raise HTTPException(status_code=400, detail=f"Error reading file: {e!s}") from e

	try:
		orders, errors = OrderService.detect_and_parse_csv(content_str)
		if not orders and errors:
			return {
				"success": False,
				"imported_count": 0,
				"skipped_count": 0,
				"updated_count": 0,
				"errors": errors,
				"message": "No orders were imported due to errors",
			}

		new_count, skipped_count = OrderService.import_orders_atomic(current_user.username, orders)

		if new_count:
			manager = get_websocket_manager()
			await manager.broadcast_to_user(
				current_user.username,
				{"type": "orders_imported", "count": new_count, "timestamp": datetime.now(UTC).isoformat()},
			)

		return {
			"success": True,
			"imported_count": new_count,
			"updated_count": 0,
			"skipped_count": skipped_count,
			"errors": errors,
			"message": f"Successfully imported {new_count} new orders and skipped {skipped_count} already-present orders",
		}
	except Exception as e:
		logger.error(f"Unexpected error in import_csv: {e}")
		raise HTTPException(status_code=500, detail=f"Error processing CSV: {e!s}") from e


@router.post("/import-csv/preview")
async def preview_import_csv(
	file: UploadFile = File(...),
	current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
	"""Preview a CSV import and classify orders as new or already present."""
	logger.info(f"CSV import preview started - User: {current_user.username}, File: {file.filename}")

	if not file.filename.endswith(".csv"):
		raise HTTPException(status_code=400, detail="File must be a CSV")

	try:
		content = await file.read()
		content_str = content.decode("utf-8")
	except Exception as e:
		raise HTTPException(status_code=400, detail=f"Error reading file: {e!s}") from e

	try:
		orders, errors = OrderService.detect_and_parse_csv(content_str)
		existing_orders = OrderService.get_user_orders(current_user.username)["orders"]
		classification = OrderService.classify_import_orders(existing_orders, orders)

		return {
			"success": True,
			"orders": classification["orders"],
			"new_count": classification["new_count"],
			"skipped_count": classification["skipped_count"],
			"errors": errors,
		}
	except Exception as e:
		logger.error(f"Unexpected error in preview_import_csv: {e}")
		raise HTTPException(status_code=500, detail=f"Error processing CSV preview: {e!s}") from e


@router.get("/")
async def get_orders(
	current_user: User = Depends(get_current_user),
	isin: str | None = Query(None),
	ticker: str | None = Query(None),
	order_type: str | None = Query(None),
	status: str | None = Query(None),
	date_from: str | None = Query(None),
	date_to: str | None = Query(None),
	sort_by: str = Query("date"),
	sort_order: str = Query("desc"),
	limit: int | None = Query(None),
	offset: int = Query(0),
) -> dict[str, Any]:
	"""Get orders for current user with filtering, sorting, and pagination."""
	return OrderService.get_user_orders(
		current_user.username,
		isin=isin,
		ticker=ticker,
		order_type=order_type,
		status=status,
		date_from=date_from,
		date_to=date_to,
		sort_by=sort_by,
		sort_order=sort_order,
		limit=limit,
		offset=offset,
	)


@router.get("/{order_id}")
async def get_order(order_id: str, current_user: User = Depends(get_current_user)) -> dict[str, Any]:
	"""Get specific order by ID."""
	order = OrderService.get_order_by_id(current_user.username, order_id)
	if not order:
		raise HTTPException(status_code=404, detail="Order not found")
	return order


@router.post("/", status_code=201)
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user)) -> OrderResponse:
	"""Create a new order manually."""
	new_order = OrderService.create_manual_order_atomic(current_user.username, order_data)

	manager = get_websocket_manager()
	await manager.broadcast_to_user(
		current_user.username,
		{"type": "order_created", "order_id": new_order["id"], "timestamp": datetime.now(UTC).isoformat()},
	)
	return OrderResponse(**new_order)


@router.put("/{order_id}")
async def update_order(
	order_id: str,
	order_data: OrderUpdate,
	current_user: User = Depends(get_current_user),
) -> OrderResponse:
	"""Update an existing order."""
	update_dict = order_data.model_dump(exclude_unset=True)
	updated_order = OrderService.update_order_atomic(current_user.username, order_id, update_dict)

	if not updated_order:
		raise HTTPException(status_code=404, detail="Order not found")

	manager = get_websocket_manager()
	await manager.broadcast_to_user(
		current_user.username,
		{"type": "order_updated", "order_id": order_id, "timestamp": datetime.now(UTC).isoformat()},
	)
	return OrderResponse(**updated_order)


@router.delete("/all", status_code=204)
async def delete_all_orders(current_user: User = Depends(get_current_user)):
	"""Delete all orders for the current user."""
	OrderService.clear_all_orders_atomic(current_user.username)

	manager = get_websocket_manager()
	await manager.broadcast_to_user(
		current_user.username,
		{"type": "orders_cleared", "timestamp": datetime.now(UTC).isoformat()},
	)


@router.delete("/{order_id}", status_code=204)
async def delete_order(order_id: str, current_user: User = Depends(get_current_user)):
	"""Delete an order."""
	deleted = OrderService.delete_order_atomic(current_user.username, order_id)
	if not deleted:
		raise HTTPException(status_code=404, detail="Order not found")

	manager = get_websocket_manager()
	await manager.broadcast_to_user(
		current_user.username,
		{"type": "order_deleted", "order_id": order_id, "timestamp": datetime.now(UTC).isoformat()},
	)
