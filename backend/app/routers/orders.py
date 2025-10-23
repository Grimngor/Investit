"""Router for order management (CSV import, CRUD operations)."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.user import User
from app.models.order import OrderCreate, OrderUpdate, OrderResponse
from app.routers.auth import get_current_user
from app.utils.csv_parser import SpanishOrderCSVParser
from app.services.storage_service import StorageService
from app.config import settings
import uuid

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
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
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    # Read file content
    try:
        content = await file.read()
        content_str = content.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    try:
        # Parse CSV
        parser = SpanishOrderCSVParser()
        orders, errors = parser.parse_csv(content_str)

        # Check for parsing errors
        if errors:
            # Return partial success with errors
            return {
                "success": True,
                "imported_count": len(orders),
                "rejected_count": len([o for o in orders if o.get("status") == "rechazada"]),
                "errors": errors,
                "message": f"Imported {len(orders)} orders with {len(errors)} errors",
            }

        # Store orders in user's data
        def add_orders(user_data):
            if "orders" not in user_data:
                user_data["orders"] = []
            user_data["orders"].extend(orders)
            # Sort by date (most recent first)
            user_data["orders"].sort(key=lambda x: x.get("date", ""), reverse=True)
            return user_data

        users_file = settings.DATA_DIR / "users.json"
        users = StorageService.load_json(users_file, default={})

        if current_user.username not in users:
            raise HTTPException(status_code=404, detail="User not found")

        users[current_user.username] = add_orders(users[current_user.username])
        StorageService.save_json(users_file, users)

        # TODO: Broadcast update via WebSocket
        # await manager.broadcast_to_user(current_user.username, {
        #     "type": "orders_imported",
        #     "count": len(orders)
        # })

        return {
            "success": True,
            "imported_count": len(orders),
            "rejected_count": len([o for o in orders if o.get("status") == "rechazada"]),
            "errors": [],
            "message": f"Successfully imported {len(orders)} orders",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")


@router.get("/")
async def get_orders(
    current_user: User = Depends(get_current_user),
    isin: Optional[str] = Query(None, description="Filter by ISIN"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    order_type: Optional[str] = Query(None, description="Filter by order type (buy/sell)"),
    status: Optional[str] = Query(None, description="Filter by status (Finalizada/Rechazada)"),
    date_from: Optional[str] = Query(None, description="Filter orders from this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter orders up to this date (YYYY-MM-DD)"),
    sort_by: str = Query("date", description="Sort by field: date, amount_eur, shares"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
) -> Dict[str, Any]:
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
    
    # Apply filters
    filtered_orders = orders
    
    if isin:
        filtered_orders = [o for o in filtered_orders if o.get("isin", "").upper() == isin.upper()]
    
    if ticker:
        filtered_orders = [o for o in filtered_orders if o.get("ticker", "").upper() == ticker.upper()]
    
    if order_type:
        filtered_orders = [o for o in filtered_orders if o.get("order_type", "") == order_type.lower()]
    
    if status:
        filtered_orders = [o for o in filtered_orders if o.get("status", "").lower() == status.lower()]
    
    if date_from:
        filtered_orders = [o for o in filtered_orders if o.get("date", "") >= date_from]
    
    if date_to:
        filtered_orders = [o for o in filtered_orders if o.get("date", "") <= date_to]
    
    # Sort orders
    reverse = sort_order.lower() == "desc"
    
    if sort_by in ["date", "amount_eur", "shares"]:
        filtered_orders.sort(
            key=lambda x: x.get(sort_by, 0 if sort_by != "date" else ""),
            reverse=reverse
        )
    
    total_count = len(filtered_orders)
    
    # Apply pagination
    paginated_orders = filtered_orders[offset:]
    if limit:
        paginated_orders = paginated_orders[:limit]
    
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
            "date_to": date_to
        },
        "sort": {
            "by": sort_by,
            "order": sort_order
        }
    }



@router.get("/{order_id}")
async def get_order(order_id: str, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
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
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user)
) -> OrderResponse:
    """
    Create a new order manually.
    
    This allows users to add individual buy/sell orders without CSV import.
    """
    users_file = settings.DATA_DIR / "users.json"
    users = StorageService.load_json(users_file, default={})

    if current_user.username not in users:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate unique order ID
    order_id = str(uuid.uuid4())
    
    # Create order with ID and timestamp
    new_order = {
        "id": order_id,
        "date": order_data.date,
        "isin": order_data.isin,
        "ticker": order_data.ticker,
        "amount_eur": order_data.amount_eur,
        "shares": order_data.shares,
        "order_type": order_data.order_type,
        "status": order_data.status,
        "notes": order_data.notes,
        "created_at": datetime.now().isoformat()
    }

    # Add to user's orders
    if "orders" not in users[current_user.username]:
        users[current_user.username]["orders"] = []
    
    users[current_user.username]["orders"].append(new_order)
    
    # Sort by date (most recent first)
    users[current_user.username]["orders"].sort(
        key=lambda x: x.get("date", ""), 
        reverse=True
    )

    # Save
    StorageService.save_json(users_file, users)

    return OrderResponse(**new_order)


@router.put("/{order_id}")
async def update_order(
    order_id: str,
    order_data: OrderUpdate,
    current_user: User = Depends(get_current_user)
) -> OrderResponse:
    """Update an existing order."""
    users_file = settings.DATA_DIR / "users.json"
    users = StorageService.load_json(users_file, default={})

    if current_user.username not in users:
        raise HTTPException(status_code=404, detail="User not found")

    orders = users[current_user.username].get("orders", [])
    
    # Find order index
    order_idx = next(
        (i for i, o in enumerate(orders) if o.get("id") == order_id), 
        None
    )
    
    if order_idx is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update order fields
    order = orders[order_idx]
    update_dict = order_data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        if value is not None:
            order[key] = value

    # Re-sort if date changed
    if "date" in update_dict:
        users[current_user.username]["orders"].sort(
            key=lambda x: x.get("date", ""), 
            reverse=True
        )

    # Save
    StorageService.save_json(users_file, users)

    return OrderResponse(**order)


@router.delete("/{order_id}", status_code=204)
async def delete_order(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an order."""
    users_file = settings.DATA_DIR / "users.json"
    users = StorageService.load_json(users_file, default={})

    if current_user.username not in users:
        raise HTTPException(status_code=404, detail="User not found")

    orders = users[current_user.username].get("orders", [])
    
    # Find and remove order
    order_idx = next(
        (i for i, o in enumerate(orders) if o.get("id") == order_id), 
        None
    )
    
    if order_idx is None:
        raise HTTPException(status_code=404, detail="Order not found")

    orders.pop(order_idx)

    # Save
    StorageService.save_json(users_file, users)

    return None  # 204 No Content

