"""Gmail API integration for MyInvestor order imports."""

import base64
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt

from app.config import settings
from app.models.gmail_import import GmailImportPreviewOrder, GmailScanResponse
from app.services.database_service import DatabaseService
from app.services.order_service import OrderService
from app.utils.myinvestor_email_parser import MyInvestorEmailParseError, MyInvestorEmailParser, MyInvestorParsedOrder


class GmailImportError(RuntimeError):
	"""Raised when Gmail import setup or API calls fail."""


class GmailImportService:
	"""Service for Gmail OAuth, message scanning, and MyInvestor order importing."""

	AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
	TOKEN_URL = "https://oauth2.googleapis.com/token"
	GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
	PROFILE_URL = f"{GMAIL_API_BASE}/users/me/profile"
	USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
	SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
	LOGIN_SCOPE = f"openid email profile {SCOPE}"

	def __init__(self, db: DatabaseService | None = None, parser: MyInvestorEmailParser | None = None) -> None:
		"""Initialize the service."""
		self.db = db or DatabaseService()
		self.parser = parser or MyInvestorEmailParser()

	def is_configured(self) -> bool:
		"""Return True when Google OAuth settings are present."""
		return bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)

	def connection_status(self, username: str) -> dict[str, Any]:
		"""Return Gmail connection status for a user."""
		connection = self.get_connection(username)
		return {
			"configured": self.is_configured(),
			"connected": connection is not None,
			"email": connection.get("email") if connection else None,
			"scope": connection.get("scope") if connection else None,
			"query": settings.GMAIL_IMPORT_QUERY,
			"max_messages": self.default_max_messages(username),
		}

	def build_auth_url(self, username: str, redirect_uri: str, return_path: str = "/portfolio") -> str:
		"""Build a Google OAuth authorization URL for the current user."""
		if not self.is_configured():
			raise GmailImportError("Google OAuth is not configured.")

		state = jwt.encode(
			{
				"sub": username,
				"return_path": return_path if return_path.startswith("/") else "/portfolio",
				"exp": datetime.now(UTC) + timedelta(minutes=15),
			},
			settings.SECRET_KEY,
			algorithm=settings.ALGORITHM,
		)
		params = {
			"client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
			"redirect_uri": self.effective_redirect_uri(redirect_uri),
			"response_type": "code",
			"scope": self.SCOPE,
			"access_type": "offline",
			"prompt": "consent",
			"state": state,
		}
		return f"{self.AUTH_URL}?{urlencode(params)}"

	def build_google_login_auth_url(self, redirect_uri: str, return_path: str = "/dashboard") -> str:
		"""Build a Google OAuth URL for app login/register plus Gmail import consent."""
		if not self.is_configured():
			raise GmailImportError("Google OAuth is not configured.")

		state = jwt.encode(
			{
				"kind": "google_login",
				"return_path": return_path if return_path.startswith("/") else "/dashboard",
				"exp": datetime.now(UTC) + timedelta(minutes=15),
			},
			settings.SECRET_KEY,
			algorithm=settings.ALGORITHM,
		)
		params = {
			"client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
			"redirect_uri": self.effective_google_login_redirect_uri(redirect_uri),
			"response_type": "code",
			"scope": self.LOGIN_SCOPE,
			"access_type": "offline",
			"prompt": "select_account",
			"include_granted_scopes": "true",
			"state": state,
		}
		return f"{self.AUTH_URL}?{urlencode(params)}"

	def parse_state(self, state: str) -> dict[str, Any]:
		"""Decode and validate an OAuth state token."""
		try:
			payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
		except JWTError as exc:
			raise GmailImportError("Invalid Gmail OAuth state.") from exc
		if not payload.get("sub"):
			raise GmailImportError("Invalid Gmail OAuth state.")
		return payload

	def parse_login_state(self, state: str) -> dict[str, Any]:
		"""Decode and validate a Google login OAuth state token."""
		try:
			payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
		except JWTError as exc:
			raise GmailImportError("Invalid Google OAuth state.") from exc
		if payload.get("kind") != "google_login":
			raise GmailImportError("Invalid Google OAuth state.")
		return payload

	async def complete_oauth(self, username: str, code: str, redirect_uri: str) -> None:
		"""Exchange an OAuth code and store the Gmail connection."""
		token_payload = await self._post_token(
			{
				"client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
				"client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
				"code": code,
				"grant_type": "authorization_code",
				"redirect_uri": self.effective_redirect_uri(redirect_uri),
			}
		)
		refresh_token = token_payload.get("refresh_token")
		access_token = token_payload.get("access_token")
		if not refresh_token or not access_token:
			raise GmailImportError("Google did not return a refresh token. Reconnect Gmail and approve offline access.")

		profile = await self._get_json(self.PROFILE_URL, access_token)
		email = str(profile.get("emailAddress") or "")
		self.save_connection(
			username,
			{
				"email": email,
				"scope": token_payload.get("scope", self.SCOPE),
				"encrypted_refresh_token": self.encrypt_token(refresh_token),
				"connected_at": datetime.now(UTC).isoformat(),
				"updated_at": datetime.now(UTC).isoformat(),
			},
		)

	async def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
		"""Exchange a Google OAuth authorization code for tokens."""
		return await self._post_token(
			{
				"client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
				"client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
				"code": code,
				"grant_type": "authorization_code",
				"redirect_uri": redirect_uri,
			}
		)

	async def userinfo(self, access_token: str) -> dict[str, Any]:
		"""Fetch Google OpenID user profile information."""
		if not access_token:
			raise GmailImportError("Google did not return an access token.")
		return await self._get_json(self.USERINFO_URL, access_token)

	async def scan(self, username: str, query: str | None = None, max_messages: int | None = None) -> GmailScanResponse:
		"""Scan Gmail for MyInvestor order emails and return import previews."""
		access_token = await self.access_token(username)
		message_ids = await self.list_message_ids(
			access_token,
			query=query or settings.GMAIL_IMPORT_QUERY,
			max_messages=max_messages or self.default_max_messages(username),
		)
		processed_ids = self.processed_message_ids(username)
		already_processed_count = 0
		parsed_orders: list[MyInvestorParsedOrder] = []
		errors: list[str] = []

		for message_id in message_ids:
			if message_id in processed_ids:
				already_processed_count += 1
				continue
			try:
				message = await self.get_message(access_token, message_id)
				parsed_orders.append(self.parse_gmail_message(message))
			except (GmailImportError, MyInvestorEmailParseError) as exc:
				errors.append(f"{message_id}: {exc}")

		existing_orders = OrderService.get_user_orders(username)["orders"]
		classified = OrderService.classify_import_orders(existing_orders, [parsed.order for parsed in parsed_orders])
		preview_orders = [
			self._preview_from_parsed(parsed, classified_order)
			for parsed, classified_order in zip(parsed_orders, classified["orders"], strict=False)
		]

		return GmailScanResponse(
			success=True,
			orders=preview_orders,
			errors=errors,
			new_count=classified["new_count"],
			skipped_count=classified["skipped_count"],
			needs_review_count=classified["needs_review_count"] + len(errors),
			already_processed_count=already_processed_count,
		)

	async def import_messages(self, username: str, gmail_message_ids: list[str]) -> dict[str, Any]:
		"""Import selected Gmail messages after re-fetching and parsing them server-side."""
		access_token = await self.access_token(username)
		imported_count = 0
		skipped_count = 0
		error_count = 0
		errors: list[str] = []

		for message_id in gmail_message_ids:
			if self.import_record(username, message_id):
				skipped_count += 1
				continue

			try:
				parsed = self.parse_gmail_message(await self.get_message(access_token, message_id))
				existing_orders = OrderService.get_user_orders(username)["orders"]
				classification = OrderService.classify_import_orders(existing_orders, [parsed.order])["orders"][0]
				if classification["import_status"] == "already_present":
					self.record_import(username, parsed, status="skipped_duplicate", order_id=classification.get("existing_order_id"))
					skipped_count += 1
					continue

				new_count, skipped = OrderService.import_orders_atomic(username, [parsed.order])
				if new_count:
					self.record_import(username, parsed, status="imported", order_id=parsed.order["id"])
					imported_count += 1
				else:
					self.record_import(username, parsed, status="skipped_duplicate")
					skipped_count += skipped
			except (GmailImportError, MyInvestorEmailParseError) as exc:
				error_count += 1
				errors.append(f"{message_id}: {exc}")

		return {
			"success": error_count == 0,
			"imported_count": imported_count,
			"skipped_count": skipped_count,
			"error_count": error_count,
			"errors": errors,
			"message": f"Imported {imported_count} Gmail order(s), skipped {skipped_count}, errors {error_count}.",
		}

	async def access_token(self, username: str) -> str:
		"""Return a fresh access token for the user's Gmail connection."""
		connection = self.get_connection(username)
		if not connection:
			raise GmailImportError("Gmail is not connected.")
		refresh_token = self.decrypt_token(connection["encrypted_refresh_token"])
		token_payload = await self._post_token(
			{
				"client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
				"client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
				"refresh_token": refresh_token,
				"grant_type": "refresh_token",
			}
		)
		access_token = token_payload.get("access_token")
		if not access_token:
			raise GmailImportError("Google did not return an access token.")
		return str(access_token)

	async def list_message_ids(self, access_token: str, query: str, max_messages: int) -> list[str]:
		"""List Gmail message IDs for a search query."""
		response = await self._get_json(
			f"{self.GMAIL_API_BASE}/users/me/messages",
			access_token,
			params={"q": query, "maxResults": max_messages},
		)
		return [str(message["id"]) for message in response.get("messages", []) if message.get("id")]

	def default_max_messages(self, username: str) -> int:
		"""Return the default scan size, using a larger first Gmail backfill."""
		if self.processed_message_ids(username):
			return settings.GMAIL_IMPORT_MAX_MESSAGES
		return settings.GMAIL_IMPORT_INITIAL_MAX_MESSAGES

	async def get_message(self, access_token: str, message_id: str) -> dict[str, Any]:
		"""Fetch a Gmail message with full payload data."""
		return await self._get_json(
			f"{self.GMAIL_API_BASE}/users/me/messages/{message_id}",
			access_token,
			params={"format": "full"},
		)

	def parse_gmail_message(self, message: dict[str, Any]) -> MyInvestorParsedOrder:
		"""Parse a Gmail API message into a MyInvestor order."""
		payload = message.get("payload", {})
		headers = {header.get("name", "").lower(): header.get("value", "") for header in payload.get("headers", [])}
		message_text = self._payload_text(payload)
		return self.parser.parse_message(
			gmail_message_id=str(message.get("id", "")),
			gmail_thread_id=str(message.get("threadId", "")),
			email_date=str(headers.get("date", "")),
			email_from=str(headers.get("from", "")),
			email_subject=str(headers.get("subject", "")),
			message_text=message_text,
		)

	def effective_redirect_uri(self, fallback_redirect_uri: str) -> str:
		"""Return configured redirect URI or the request-derived fallback."""
		return settings.GMAIL_OAUTH_REDIRECT_URI or fallback_redirect_uri

	def effective_google_login_redirect_uri(self, fallback_redirect_uri: str) -> str:
		"""Return configured Google login redirect URI or the request-derived fallback."""
		return settings.GOOGLE_LOGIN_REDIRECT_URI or fallback_redirect_uri

	def get_connection(self, username: str) -> dict[str, Any] | None:
		"""Load a user's Gmail connection."""
		self.db.initialize()
		with self.db.connect() as conn:
			row = conn.execute("SELECT connection_json FROM gmail_connections WHERE username = ?", (username,)).fetchone()
			return json.loads(row["connection_json"]) if row else None

	def save_connection(self, username: str, connection: dict[str, Any]) -> None:
		"""Persist a user's Gmail connection."""
		self.db.initialize()
		with self.db.connect() as conn, conn:
			conn.execute(
				"INSERT OR REPLACE INTO gmail_connections (username, connection_json) VALUES (?, ?)",
				(username, json.dumps(connection, ensure_ascii=False)),
			)

	def disconnect(self, username: str) -> None:
		"""Delete a user's Gmail connection."""
		self.db.initialize()
		with self.db.connect() as conn, conn:
			conn.execute("DELETE FROM gmail_connections WHERE username = ?", (username,))

	def processed_message_ids(self, username: str) -> set[str]:
		"""Return Gmail message IDs already recorded for a user."""
		self.db.initialize()
		with self.db.connect() as conn:
			rows = conn.execute("SELECT gmail_message_id FROM gmail_imports WHERE username = ?", (username,))
			return {str(row["gmail_message_id"]) for row in rows}

	def import_record(self, username: str, gmail_message_id: str) -> dict[str, Any] | None:
		"""Return an import record for a Gmail message ID when present."""
		self.db.initialize()
		with self.db.connect() as conn:
			row = conn.execute(
				"SELECT import_json FROM gmail_imports WHERE username = ? AND gmail_message_id = ?",
				(username, gmail_message_id),
			).fetchone()
			return json.loads(row["import_json"]) if row else None

	def record_import(
		self,
		username: str,
		parsed: MyInvestorParsedOrder,
		*,
		status: str,
		order_id: str | None = None,
		error_message: str = "",
	) -> None:
		"""Persist the result of processing one Gmail message."""
		record = {
			"gmail_message_id": parsed.gmail_message_id,
			"gmail_thread_id": parsed.gmail_thread_id,
			"email_date": parsed.email_date,
			"email_from": parsed.email_from,
			"email_subject": parsed.email_subject,
			"parsed_hash": self.parsed_hash(parsed.order),
			"order_id": order_id,
			"status": status,
			"error_message": error_message,
			"created_at": datetime.now(UTC).isoformat(),
		}
		self.db.initialize()
		with self.db.connect() as conn, conn:
			conn.execute(
				"INSERT OR REPLACE INTO gmail_imports (username, gmail_message_id, import_json) VALUES (?, ?, ?)",
				(username, parsed.gmail_message_id, json.dumps(record, ensure_ascii=False)),
			)

	def now_iso(self) -> str:
		"""Return the current UTC timestamp as an ISO string."""
		return datetime.now(UTC).isoformat()

	def parsed_hash(self, order: dict[str, Any]) -> str:
		"""Return a stable hash for parsed order content."""
		fingerprint = OrderService.order_fingerprint(order)
		return hashlib.sha256("|".join(fingerprint).encode("utf-8")).hexdigest()

	def encrypt_token(self, token: str) -> str:
		"""Encrypt an OAuth token for storage."""
		return self._fernet().encrypt(token.encode("utf-8")).decode("utf-8")

	def decrypt_token(self, encrypted_token: str) -> str:
		"""Decrypt an OAuth token from storage."""
		try:
			return self._fernet().decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
		except InvalidToken as exc:
			raise GmailImportError("Stored Gmail token could not be decrypted.") from exc

	def _preview_from_parsed(
		self,
		parsed: MyInvestorParsedOrder,
		classified_order: dict[str, Any],
	) -> GmailImportPreviewOrder:
		"""Build a preview schema from a parsed order and classification."""
		return GmailImportPreviewOrder(
			gmail_message_id=parsed.gmail_message_id,
			gmail_thread_id=parsed.gmail_thread_id,
			email_date=parsed.email_date,
			email_from=parsed.email_from,
			email_subject=parsed.email_subject,
			operation_type=parsed.operation_type,
			value_date=parsed.value_date,
			unit_price=parsed.unit_price,
			amount_gross=parsed.amount_gross,
			amount_net=parsed.amount_net,
			import_status=classified_order.get("import_status", "new"),
			existing_order_id=classified_order.get("existing_order_id"),
			order=classified_order,
		)

	def _payload_text(self, payload: dict[str, Any]) -> str:
		"""Extract visible text from a Gmail message payload."""
		content_type = str(payload.get("mimeType", ""))
		body_text = self._decode_body(payload.get("body", {}).get("data"))
		parts = payload.get("parts") or []
		child_text = "\n".join(self._payload_text(part) for part in parts)
		text = "\n".join(part for part in (body_text, child_text) if part)
		return self.parser.html_to_text(text) if content_type == "text/html" else self.parser.normalize_text(text)

	def _decode_body(self, data: str | None) -> str:
		"""Decode a Gmail base64url body payload."""
		if not data:
			return ""
		padding = "=" * (-len(data) % 4)
		try:
			return base64.urlsafe_b64decode(f"{data}{padding}").decode("utf-8", errors="replace")
		except (ValueError, UnicodeDecodeError):
			return ""

	async def _post_token(self, data: dict[str, str]) -> dict[str, Any]:
		"""Post to Google's OAuth token endpoint."""
		async with httpx.AsyncClient(timeout=15.0) as client:
			response = await client.post(self.TOKEN_URL, data=data)
		if response.status_code >= 400:
			raise GmailImportError(f"Google token request failed: {response.text}")
		return response.json()

	async def _get_json(self, url: str, access_token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
		"""GET JSON from a Google API endpoint."""
		headers = {"Authorization": f"Bearer {access_token}"}
		async with httpx.AsyncClient(timeout=20.0) as client:
			response = await client.get(url, headers=headers, params=params)
		if response.status_code >= 400:
			raise GmailImportError(f"Gmail API request failed: {response.text}")
		return response.json()

	def _fernet(self) -> Fernet:
		"""Return a Fernet instance derived from the app secret key."""
		digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
		return Fernet(base64.urlsafe_b64encode(digest))
