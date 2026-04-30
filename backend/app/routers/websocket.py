"""WebSocket router for real-time updates and broadcast helper."""

import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.config import settings
from app.services.metrics_service import metrics

router = APIRouter(tags=["websocket"])


class WebSocketManager:
	"""In-memory WebSocket connection manager per username."""

	def __init__(self) -> None:
		self._connections: dict[str, list[WebSocket]] = {}

	async def connect(self, username: str, websocket: WebSocket) -> None:
		self._connections.setdefault(username, []).append(websocket)
		metrics.increment_websockets()

	async def disconnect(self, username: str, websocket: WebSocket) -> None:
		conns = self._connections.get(username, [])
		if websocket in conns:
			conns.remove(websocket)
			metrics.decrement_websockets()
		if not conns:
			self._connections.pop(username, None)

	async def broadcast_to_user(self, username: str, message: dict[str, Any]) -> None:
		for ws in self._connections.get(username, []):
			try:
				await ws.send_json(message)
			except Exception:
				# Drop failing connection silently
				await self.disconnect(username, ws)


manager = WebSocketManager()


async def decode_token(token: str) -> str | None:
	"""Decode JWT token and return username."""
	try:
		payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
		username: str = payload.get("sub")
		return username
	except JWTError:
		return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
	"""
	WebSocket endpoint authenticated by the first client message.

	Connect to /ws, then send {"type": "auth", "token": "<jwt>"}.
	"""
	await websocket.accept()
	username: str | None = None
	connected = False

	try:
		auth_message = await websocket.receive_json()
	except WebSocketDisconnect:
		return
	except Exception:
		await websocket.close(code=1008, reason="Invalid authentication message")
		return

	token = auth_message.get("token") if isinstance(auth_message, dict) and auth_message.get("type") == "auth" else None
	if not isinstance(token, str) or not token:
		await websocket.close(code=1008, reason="Missing authentication token")
		return

	username = await decode_token(token)
	if not username:
		await websocket.close(code=1008, reason="Invalid authentication token")
		return

	await manager.connect(username, websocket)
	connected = True

	# Send handshake message
	try:
		await websocket.send_json(
			{
				"type": "connection_status",
				"status": "connected",
				"client_id": username,
				"timestamp": datetime.datetime.now().isoformat(),
			}
		)
	except (WebSocketDisconnect, RuntimeError):
		await manager.disconnect(username, websocket)
		return

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
		pass
	finally:
		if connected and username:
			await manager.disconnect(username, websocket)
