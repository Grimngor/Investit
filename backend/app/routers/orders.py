"""Router for order management (CSV import, CRUD operations)."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
from app.models.user import User
from app.routers.auth import get_current_user
from app.utils.csv_parser import SpanishOrderCSVParser
from app.services.storage_service import StorageService
from app.config import settings

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
async def get_orders(current_user: User = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """
    Get all orders for current user.

    Returns:
        List of orders sorted by date (most recent first)
    """
    users_file = settings.DATA_DIR / "users.json"
    users = StorageService.load_json(users_file, default={})

    if current_user.username not in users:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = users[current_user.username]
    orders = user_data.get("orders", [])

    return orders


@router.get("/{order_id}")
async def get_order(order_id: int, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Get specific order by ID."""
    users_file = settings.DATA_DIR / "users.json"
    users = StorageService.load_json(users_file, default={})

    if current_user.username not in users:
        raise HTTPException(status_code=404, detail="User not found")

    orders = users[current_user.username].get("orders", [])

    if order_id < 0 or order_id >= len(orders):
        raise HTTPException(status_code=404, detail="Order not found")

    return orders[order_id]
