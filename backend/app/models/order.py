"""Order and related models for the investment tracking system."""

from pydantic import BaseModel, Field


class Order(BaseModel):
	"""
	Represents a buy/sell order for an investment instrument.

	Based on PRD Section 3: Order-based data model.
	"""

	id: str | None = None
	date: str = Field(..., description="Order execution date in YYYY-MM-DD format")
	isin: str = Field(..., min_length=12, max_length=12, description="ISIN code (12 characters)")
	ticker: str | None = Field(None, description="Optional ticker symbol")
	amount_eur: float = Field(..., gt=0, description="Order amount in EUR")
	shares: float = Field(..., gt=0, description="Number of shares/units")
	price_per_share: float | None = Field(None, description="Price per share at order execution")
	price_currency: str | None = Field(None, description="Currency of the price")
	price_date: str | None = Field(None, description="Date of the price used")
	order_type: str = Field("buy", description="Order type: buy or sell")
	status: str = Field("Finalizada", description="Order status: Finalizada or Rechazada")
	notes: str = Field("", description="Optional notes")
	created_at: str | None = None


class OrderCreate(BaseModel):
	"""Schema for creating a new order manually."""

	date: str
	isin: str = Field(..., min_length=12, max_length=12)
	ticker: str | None = None
	amount_eur: float = Field(..., gt=0)
	shares: float = Field(..., gt=0)
	price_per_share: float | None = None
	price_currency: str | None = None
	price_date: str | None = None
	order_type: str = "buy"
	status: str = "Finalizada"
	notes: str = ""


class OrderUpdate(BaseModel):
	"""Schema for updating an existing order."""

	date: str | None = None
	isin: str | None = None
	ticker: str | None = None
	amount_eur: float | None = None
	shares: float | None = None
	price_per_share: float | None = None
	price_currency: str | None = None
	price_date: str | None = None
	order_type: str | None = None
	status: str | None = None
	notes: str | None = None


class OrderResponse(BaseModel):
	"""Response schema for order operations."""

	id: str
	date: str
	isin: str
	ticker: str | None
	amount_eur: float
	shares: float
	order_type: str
	status: str
	notes: str
	created_at: str


class Instrument(BaseModel):
	"""
	Represents an investment instrument (ETF, fund, stock).

	Separate from orders per PRD architecture.
	"""

	isin: str = Field(..., min_length=12, max_length=12)
	ticker: str
	name: str
	instrument_type: str = Field(..., description="ETF, Index Fund, Stock, Bond")
	currency: str = "EUR"
	sector: str | None = None
	region: str | None = None
	geography: str | None = None
	risk_rating: str | None = None


class Price(BaseModel):
	"""
	Current price for an instrument.

	Separate collection per PRD.
	"""

	isin: str
	ticker: str
	price: float
	currency: str = "EUR"
	timestamp: str
	source: str = "finnhub"


class UserSettings(BaseModel):
	"""User-specific settings."""

	username: str
	default_currency: str = "EUR"
	theme: str = "light"
	notifications_enabled: bool = True
