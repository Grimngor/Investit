"""Router for Gmail-backed MyInvestor order imports."""

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.models.gmail_import import (
	GmailAuthUrlResponse,
	GmailConnectionStatus,
	GmailImportRequest,
	GmailImportResponse,
	GmailScanRequest,
	GmailScanResponse,
)
from app.models.user import User
from app.routers.auth import get_current_user
from app.routers.websocket import manager as websocket_manager
from app.services.gmail_import_service import GmailImportError, GmailImportService

router = APIRouter(prefix="/api/gmail", tags=["gmail"])


def get_gmail_import_service() -> GmailImportService:
	"""Return a Gmail import service instance."""
	return GmailImportService()


@router.get("/status", response_model=GmailConnectionStatus)
async def status_endpoint(
	current_user: User = Depends(get_current_user),
	service: GmailImportService = Depends(get_gmail_import_service),
) -> dict:
	"""Return Gmail import connection status."""
	return service.connection_status(current_user.username)


@router.get("/auth-url", response_model=GmailAuthUrlResponse)
async def auth_url_endpoint(
	request: Request,
	return_path: str = "/portfolio",
	current_user: User = Depends(get_current_user),
	service: GmailImportService = Depends(get_gmail_import_service),
) -> dict[str, str]:
	"""Return a Google OAuth authorization URL."""
	try:
		redirect_uri = str(request.url_for("oauth_callback_endpoint"))
		return {"auth_url": service.build_auth_url(current_user.username, redirect_uri, return_path)}
	except GmailImportError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/oauth/callback", name="oauth_callback_endpoint")
async def oauth_callback_endpoint(
	request: Request,
	code: str | None = None,
	state: str | None = None,
	error: str | None = None,
	service: GmailImportService = Depends(get_gmail_import_service),
) -> RedirectResponse:
	"""Handle Google's OAuth callback for Gmail connection."""
	return_path = "/portfolio"
	params: dict[str, str] = {}
	try:
		if error:
			raise GmailImportError(error)
		if not code or not state:
			raise GmailImportError("Missing Google OAuth callback parameters.")
		state_payload = service.parse_state(state)
		username = str(state_payload["sub"])
		return_path = str(state_payload.get("return_path") or "/portfolio")
		await service.complete_oauth(username, code, str(request.url_for("oauth_callback_endpoint")))
		params["gmail"] = "connected"
	except GmailImportError as exc:
		params["gmail"] = "error"
		params["message"] = str(exc)

	separator = "&" if "?" in return_path else "?"
	return RedirectResponse(f"{return_path}{separator}{urlencode(params)}")


@router.post("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_endpoint(
	current_user: User = Depends(get_current_user),
	service: GmailImportService = Depends(get_gmail_import_service),
) -> None:
	"""Disconnect Gmail for the current user."""
	service.disconnect(current_user.username)


@router.post("/scan", response_model=GmailScanResponse)
async def scan_endpoint(
	payload: GmailScanRequest,
	current_user: User = Depends(get_current_user),
	service: GmailImportService = Depends(get_gmail_import_service),
) -> GmailScanResponse:
	"""Scan Gmail for MyInvestor order emails."""
	try:
		return await service.scan(current_user.username, query=payload.query, max_messages=payload.max_messages)
	except GmailImportError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/import", response_model=GmailImportResponse)
async def import_endpoint(
	payload: GmailImportRequest,
	current_user: User = Depends(get_current_user),
	service: GmailImportService = Depends(get_gmail_import_service),
) -> dict:
	"""Import selected Gmail messages as orders."""
	if not payload.gmail_message_ids:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Gmail messages selected.")

	try:
		result = await service.import_messages(current_user.username, payload.gmail_message_ids)
	except GmailImportError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	if result["imported_count"]:
		await websocket_manager.broadcast_to_user(
			current_user.username,
			{"type": "orders_imported", "count": result["imported_count"]},
		)
	return result
