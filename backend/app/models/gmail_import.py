"""Schemas for Gmail-backed MyInvestor order imports."""

from pydantic import BaseModel, Field


class GmailConnectionStatus(BaseModel):
	"""Status of the current user's Gmail integration."""

	configured: bool
	connected: bool
	email: str | None = None
	scope: str | None = None
	query: str
	max_messages: int


class GmailAuthUrlResponse(BaseModel):
	"""OAuth authorization URL for connecting Gmail."""

	auth_url: str


class GmailImportPreviewOrder(BaseModel):
	"""Parsed Gmail order preview row."""

	gmail_message_id: str
	gmail_thread_id: str
	email_date: str
	email_from: str
	email_subject: str
	operation_type: str
	value_date: str | None = None
	unit_price: float
	amount_gross: float
	amount_net: float | None = None
	import_status: str
	existing_order_id: str | None = None
	error: str | None = None
	order: dict


class GmailScanRequest(BaseModel):
	"""Request to scan Gmail for MyInvestor order emails."""

	query: str | None = None
	max_messages: int | None = Field(None, ge=1, le=100)


class GmailScanResponse(BaseModel):
	"""Response containing Gmail order import preview rows."""

	success: bool
	orders: list[GmailImportPreviewOrder]
	errors: list[str]
	new_count: int
	skipped_count: int
	needs_review_count: int
	already_processed_count: int


class GmailImportRequest(BaseModel):
	"""Request to import selected Gmail messages."""

	gmail_message_ids: list[str] = Field(default_factory=list)


class GmailImportResponse(BaseModel):
	"""Response for selected Gmail message import."""

	success: bool
	imported_count: int
	skipped_count: int
	error_count: int
	errors: list[str]
	message: str
