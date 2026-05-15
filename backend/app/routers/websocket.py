"""WebSocket router for real-time updates and broadcast helper."""

import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.config import settings
from app.services.auth import decode_trusted_proxy_header, find_user_by_trusted_proxy_email, is_trusted_proxy_email_allowed
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


async def get_trusted_proxy_username(websocket: WebSocket) -> str | None:
	"""Return the trusted proxy user for a WebSocket request when headers are valid."""
	if not settings.TRUSTED_PROXY_AUTH_ENABLED:
		return None

	raw_email = websocket.headers.get(settings.TRUSTED_PROXY_AUTH_HEADER_EMAIL)
	if raw_email is None:
		return None

	email = decode_trusted_proxy_header(raw_email)
	if not email or not is_trusted_proxy_email_allowed(email):
		await websocket.close(code=1008, reason="Trusted proxy identity is not allowed")
		return None

	user = find_user_by_trusted_proxy_email(email)
	if not user or user.disabled:
		await websocket.close(code=1008, reason="Trusted proxy identity is not linked to an active app user")
		return None

	return user.username


async def send_connection_status(websocket: WebSocket, username: str) -> bool:
	"""Send the standard WebSocket connection status message."""
	try:
		await websocket.send_json(
			{
				"type": "connection_status",
				"status": "connected",
				"client_id": username,
				"timestamp": datetime.datetime.now().isoformat(),
			}
		)
		return True
	except (WebSocketDisconnect, RuntimeError):
		return False


async def get_jwt_message_username(websocket: WebSocket) -> str | None:
	"""Return username from the first WebSocket JWT auth message."""
	try:
		auth_message = await websocket.receive_json()
	except WebSocketDisconnect:
		return None
	except Exception:
		await websocket.close(code=1008, reason="Invalid authentication message")
		return None

	token = auth_message.get("token") if isinstance(auth_message, dict) and auth_message.get("type") == "auth" else None
	if not isinstance(token, str) or not token:
		await websocket.close(code=1008, reason="Missing authentication token")
		return None

	username = await decode_token(token)
	if not username:
		await websocket.close(code=1008, reason="Invalid authentication token")
		return None

	return username


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
	"""
	WebSocket endpoint authenticated by the first client message.

	Connect to /ws, then send {"type": "auth", "token": "<jwt>"}.
	"""
	await websocket.accept()
	username: str | None = None
	connected = False

	has_trusted_proxy_header = (
		settings.TRUSTED_PROXY_AUTH_ENABLED and websocket.headers.get(settings.TRUSTED_PROXY_AUTH_HEADER_EMAIL) is not None
	)
	username = await get_trusted_proxy_username(websocket)
	if has_trusted_proxy_header and not username:
		return
	if not username:
		username = await get_jwt_message_username(websocket)
		if not username:
			return

	await manager.connect(username, websocket)
	connected = True

	# Send handshake message
	if not await send_connection_status(websocket, username):
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
