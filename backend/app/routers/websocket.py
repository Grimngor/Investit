"""WebSocket router for real-time updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import datetime
from jose import JWTError, jwt
from app.config import settings

router = APIRouter(tags=["websocket"])


async def decode_token(token: str) -> Optional[str]:
    """Decode JWT token and return username."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        return username
    except JWTError:
        return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    WebSocket endpoint with token-based authentication.

    Connect with: ws://localhost:8000/ws?token=YOUR_JWT_TOKEN
    """
    # Validate token before accepting connection
    if not token:
        await websocket.accept()
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    username = await decode_token(token)
    if not username:
        await websocket.accept()
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    # Accept connection
    await websocket.accept()

    # Send handshake message
    await websocket.send_json(
        {"type": "connection_status", "status": "connected", "client_id": username, "timestamp": datetime.datetime.now().isoformat()}
    )

    try:
        while True:
            data = await websocket.receive_json()

            # Handle ping/pong
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.datetime.now().isoformat()})
            else:
                # Echo back other messages
                await websocket.send_json(data)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {username}")


@router.websocket("/ws/{client_id}")
async def websocket_legacy_endpoint(websocket: WebSocket, client_id: str):
    """
    Legacy WebSocket endpoint (kept for backward compatibility).
    Prefer using /ws with token query parameter.
    """
    await websocket.accept()

    await websocket.send_json({"type": "connection_status", "status": "connected", "client_id": client_id})

    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json(data)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {client_id}")
